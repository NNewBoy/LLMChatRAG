import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/chat' },
  { path: '/chat', name: 'chat', component: () => import('../views/ChatView.vue') },
  { path: '/chat/:conversationId', name: 'chat-conversation', component: () => import('../views/ChatView.vue') },
  { path: '/rag', name: 'rag', component: () => import('../views/RAGView.vue') },
  { path: '/rag/:conversationId', name: 'rag-conversation', component: () => import('../views/RAGView.vue') },
  { path: '/documents', name: 'documents', component: () => import('../views/DocumentView.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
