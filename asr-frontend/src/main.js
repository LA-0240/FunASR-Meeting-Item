import { createApp } from 'vue'
import router from './router'
import App from './App.vue'
import axios from 'axios'

import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

const app = createApp(App)

// 配置Axios
axios.defaults.baseURL = 'http://127.0.0.1:8000'  // 后端地址
// 允许跨域请求携带Cookie（如果后端需要）
axios.defaults.withCredentials = true
axios.defaults.headers.post['Content-Type'] = 'multipart/form-data'

app.config.globalProperties.$axios = axios
app.use(ElementPlus)
app.use(router)
app.mount('#app')