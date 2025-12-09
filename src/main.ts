import { createApp } from 'vue'
import App from './App.vue'
import { createPinia } from 'pinia'
import 'vfonts/Lato.css' // naive-ui fonts
import 'vfonts/FiraCode.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.mount('#app')
