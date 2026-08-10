pipeline {
    agent any

    environment {
        ACR_REGISTRY  = "crpi-v27gqzero2fjya51.cn-guangzhou.personal.cr.aliyuncs.com"
        ACR_NAMESPACE = "chatrag"
        IMAGE_TAG     = "${BUILD_NUMBER}-${GIT_COMMIT.take(7)}"
        K8S_NAMESPACE = "app"
    }

    stages {
        stage('拉取代码') {
            steps {
                checkout scm
            }
        }

        stage('构建并推送镜像') {
            parallel {
                stage('后端服务镜像') {
                    steps {
                        script {
                            docker.withRegistry("https://${ACR_REGISTRY}", 'aliyun-acr') {
                                // ARM 架构电脑必须加 --platform linux/amd64，x86 电脑可省略
                                def img = docker.build("${ACR_NAMESPACE}/backend:${IMAGE_TAG}",
                                    "--platform linux/amd64 -f backend/Dockerfile backend/")
                                img.push()
                                img.push('latest')
                            }
                        }
                    }
                }

                stage('前端服务镜像') {
                    steps {
                        script {
                            docker.withRegistry("https://${ACR_REGISTRY}", 'aliyun-acr') {
                                def img = docker.build("${ACR_NAMESPACE}/frontend:${IMAGE_TAG}",
                                    "--platform linux/amd64 -f frontend/Dockerfile frontend/")
                                img.push()
                                img.push('latest')
                            }
                        }
                    }
                }
            }
        }

        stage('部署到 K8s 集群') {
            steps {
                withCredentials([file(credentialsId: 'k8s-kubeconfig', variable: 'KUBECONFIG')]) {
                    sh """
                        export KUBECONFIG=\$KUBECONFIG
                        # 1. 应用基础资源（首次部署需要，幂等操作）
                        kubectl apply -f k8s/namespace.yaml
                        kubectl apply -f k8s/configmap.yaml
                        kubectl apply -f k8s/pvc.yaml
                        kubectl apply -f k8s/redis.yaml
                        # 2. 先 apply Deployment/Service（不存在则创建，存在则更新）
                        kubectl apply -f k8s/backend.yaml
                        kubectl apply -f k8s/celery-worker.yaml
                        kubectl apply -f k8s/frontend.yaml
                        # 3. 滚动更新到本次构建的具体镜像标签（覆盖 yaml 中的 latest）
                        kubectl set image deployment/backend backend=${ACR_REGISTRY}/${ACR_NAMESPACE}/backend:${IMAGE_TAG} -n ${K8S_NAMESPACE}
                        kubectl set image deployment/frontend frontend=${ACR_REGISTRY}/${ACR_NAMESPACE}/frontend:${IMAGE_TAG} -n ${K8S_NAMESPACE}
                        kubectl set image deployment/celery-worker worker=${ACR_REGISTRY}/${ACR_NAMESPACE}/backend:${IMAGE_TAG} -n ${K8S_NAMESPACE}
                        # 4. 等待滚动更新完成
                        kubectl rollout status deployment/backend -n ${K8S_NAMESPACE}
                        kubectl rollout status deployment/frontend -n ${K8S_NAMESPACE}
                        kubectl rollout status deployment/celery-worker -n ${K8S_NAMESPACE}
                        # 5. 应用 Ingress（入口路由，失败不阻断核心部署）
                        #    如 ingress-nginx webhook 不可用，加 --validate=false 跳过校验
                        kubectl apply -f k8s/ingress.yaml --validate=false || echo "⚠️ Ingress 应用失败，跳过（不影响 Pod 运行，稍后可手动 kubectl apply）"
                        # 6. 固定 ingress-nginx NodePort 端口（防止 Controller 重建后端口变化）
                        kubectl patch svc ingress-nginx-controller -n ingress-nginx -p '{"spec":{"ports":[{"name":"http","port":80,"nodePort":31080,"targetPort":80},{"name":"https","port":443,"nodePort":31443,"targetPort":443}]}}' 2>/dev/null || true
                    """
                }
            }
        }
    }

    post {
        success { echo "✅ 部署成功，镜像标签：${IMAGE_TAG}" }
        failure { echo "❌ 部署失败，请查看构建日志" }
    }
}