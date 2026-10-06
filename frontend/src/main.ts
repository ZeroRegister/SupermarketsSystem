import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import { Apple, ArrowDown, ArrowRight, Bell, Bottom, Box, Food, Calendar, ChatDotRound, CircleCheck, CircleCloseFilled, Coffee, ColdDrink, Collection, DataBoard, Download, Goods, Grape, Hide, InfoFilled, Key, Lock, Message, MilkTea, Money, MoreFilled, Operation, Phone, Plus, Search, Setting, Shop, Sort, SwitchButton, Top, TrendCharts, User, Van, View, Warning, WarningFilled } from '@element-plus/icons-vue'
import 'element-plus/dist/index.css'
import './styles.css'
import './features.css'
import App from './App.vue'
import { router } from './router'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus, { size: 'large' })
Object.entries({ Apple, ArrowDown, ArrowRight, Bell, Bottom, Box, Food, Calendar, ChatDotRound, CircleCheck, CircleCloseFilled, Coffee, ColdDrink, Collection, DataBoard, Download, Goods, Grape, Hide, InfoFilled, Key, Lock, Message, MilkTea, Money, MoreFilled, Operation, Phone, Plus, Search, Setting, Shop, Sort, SwitchButton, Top, TrendCharts, User, Van, View, Warning, WarningFilled }).forEach(([key, component]) => app.component(key, component))
app.mount('#app')
