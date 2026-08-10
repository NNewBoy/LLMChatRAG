pipeline {
    agent any

    environment {
        ACR_REGISTRY  = "crpi-v27gqzero2fjya51.cn-guangzhou.personal.cr.aliyuncs.com"
        ACR_NAMESPACE = "llmproject"
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
                                def img = docker.build("${ACR_NAMESPACE}/backend_chatrag:${IMAGE_TAG}",
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
                                def img = docker.build("${ACR_NAMESPACE}/frontend_chatrag:${IMAGE_TAG}",
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
                        # 1. 应用本地业务资源（首次部署需要，幂等操作）
                        #    注意：namespace 与 redis 由 LLMBLOG 的 k8s/ 共用，不在此重复 apply
                        kubectl apply -f k8s/configmap.yaml
                        kubectl apply -f k8s/pvc.yaml
                        # 2. 先 apply Deployment/Service（不存在则创建，存在则更新）
                        kubectl apply -f k8s/backend.yaml
                        kubectl apply -f k8s/celery-worker.yaml
                        kubectl apply -f k8s/frontend.yaml
                        # 3. 滚动更新到本次构建的具体镜像标签（覆盖 yaml 中的 latest）
                        kubectl set image deployment/backend-chatrag backend-chatrag=${ACR_REGISTRY}/${ACR_NAMESPACE}/backend_chatrag:${IMAGE_TAG} -n ${K8S_NAMESPACE}
                        kubectl set image deployment/frontend-chatrag frontend-chatrag=${ACR_REGISTRY}/${ACR_NAMESPACE}/frontend_chatrag:${IMAGE_TAG} -n ${K8S_NAMESPACE}
                        kubectl set image deployment/celery-worker-chatrag worker=${ACR_REGISTRY}/${ACR_NAMESPACE}/backend_chatrag:${IMAGE_TAG} -n ${K8S_NAMESPACE}
                        # 4. 等待滚动更新完成
                        kubectl rollout status deployment/backend-chatrag -n ${K8S_NAMESPACE}
                        kubectl rollout status deployment/frontend-chatrag -n ${K8S_NAMESPACE}
                        kubectl rollout status deployment/celery-worker-chatrag -n ${K8S_NAMESPACE}
                        # 5. 应用 Ingress（入口路由，失败不阻断核心部署）
                        #    如 ingress-nginx webhook 不可用，加 --validate=false 跳过校验
                        kubectl apply -f k8s/ingress.yaml --validate=false || echo "⚠️ Ingress 应用失败，跳过（不影响 Pod 运行，稍后可手动 kubectl apply）"
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