import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import PagesView from '../views/PagesView.vue'
import PageView from '../views/PageView.vue'
import PageEditView from '../views/PageEditView.vue'
import SearchView from '../views/SearchView.vue'
import GraphView from '../views/GraphView.vue'
import EntityView from '../views/EntityView.vue'
import WeeklyView from '../views/WeeklyView.vue'
import AskView from '../views/AskView.vue'
import SkillsView from '../views/SkillsView.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/pages', name: 'pages', component: PagesView },
    { path: '/page/:path(.*)', name: 'page', component: PageView, props: true },
    { path: '/edit/:path(.*)', name: 'edit', component: PageEditView, props: true },
    { path: '/entity/:kind/:name(.*)', name: 'entity', component: EntityView, props: true },
    { path: '/search', name: 'search', component: SearchView },
    { path: '/graph', name: 'graph', component: GraphView },
    { path: '/weekly', name: 'weekly', component: WeeklyView },
    { path: '/ask', name: 'ask', component: AskView },
    { path: '/skills', name: 'skills', component: SkillsView },
  ],
})
