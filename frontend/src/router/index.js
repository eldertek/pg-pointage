import { createRouter, createWebHistory } from "vue-router"
import { useAuthStore } from "@/stores/auth"

// Layouts
import AuthLayout from "@/layouts/AuthLayout.vue"
import DashboardLayout from "@/layouts/DashboardLayout.vue"
import MobileLayout from "@/layouts/MobileLayout.vue"

// Views - Auth
import Login from "@/views/auth/Login.vue"
import ForgotPassword from "@/views/auth/ForgotPassword.vue"
import ResetPassword from "@/views/auth/ResetPassword.vue"

// Views - Dashboard (Admin/Manager)
import Dashboard from "@/views/dashboard/Dashboard.vue"
import Organizations from "@/views/dashboard/Organizations.vue"
import OrganizationDetail from "@/views/dashboard/OrganizationDetail.vue"
import Sites from "@/views/dashboard/Sites.vue"
import SiteDetail from "@/views/dashboard/SiteDetail.vue"
import Employees from "@/views/dashboard/Employees.vue"
import EmployeeDetail from "@/views/dashboard/EmployeeDetail.vue"
import Schedules from "@/views/dashboard/Schedules.vue"
import ScheduleDetail from "@/views/dashboard/ScheduleDetail.vue"
import Timesheets from "@/views/dashboard/Timesheets.vue"
import Anomalies from "@/views/dashboard/Anomalies.vue"
import Reports from "@/views/dashboard/Reports.vue"
import Settings from "@/views/dashboard/Settings.vue"

// Views - Mobile (Employee)
import MobileDashboard from "@/views/mobile/MobileDashboard.vue"
import Scan from "@/views/mobile/Scan.vue"
import History from "@/views/mobile/History.vue"
import Profile from "@/views/mobile/Profile.vue"
import ReportAnomaly from "@/views/mobile/ReportAnomaly.vue"

const routes = [
  {
    path: "/",
    redirect: "/login",
  },
  {
    path: "/",
    component: AuthLayout,
    children: [
      {
        path: "login",
        name: "Login",
        component: Login,
      },
      {
        path: "forgot-password",
        name: "ForgotPassword",
        component: ForgotPassword,
      },
      {
        path: "reset-password/:token",
        name: "ResetPassword",
        component: ResetPassword,
      },
    ],
  },
  {
    path: "/dashboard",
    component: DashboardLayout,
    meta: { requiresAuth: true, roles: ["SUPER_ADMIN", "MANAGER"] },
    children: [
      {
        path: "",
        name: "Dashboard",
        component: Dashboard,
      },
      {
        path: "organizations",
        name: "Organizations",
        component: Organizations,
        meta: { roles: ["SUPER_ADMIN"] },
      },
      {
        path: "organizations/:id",
        name: "OrganizationDetail",
        component: OrganizationDetail,
        meta: { roles: ["SUPER_ADMIN"] },
      },
      {
        path: "sites",
        name: "Sites",
        component: Sites,
      },
      {
        path: "sites/:id",
        name: "SiteDetail",
        component: SiteDetail,
      },
      {
        path: "employees",
        name: "Employees",
        component: Employees,
      },
      {
        path: "employees/:id",
        name: "EmployeeDetail",
        component: EmployeeDetail,
      },
      {
        path: "schedules",
        name: "Schedules",
        component: Schedules,
      },
      {
        path: "schedules/:id",
        name: "ScheduleDetail",
        component: ScheduleDetail,
      },
      {
        path: "timesheets",
        name: "Timesheets",
        component: Timesheets,
      },
      {
        path: "anomalies",
        name: "Anomalies",
        component: Anomalies,
      },
      {
        path: "reports",
        name: "Reports",
        component: Reports,
      },
      {
        path: "settings",
        name: "Settings",
        component: Settings,
      },
    ],
  },
  {
    path: "/mobile",
    component: MobileLayout,
    meta: { requiresAuth: true, roles: ["EMPLOYEE"] },
    children: [
      {
        path: "",
        name: "MobileDashboard",
        component: MobileDashboard,
      },
      {
        path: "scan",
        name: "Scan",
        component: Scan,
      },
      {
        path: "history",
        name: "History",
        component: History,
      },
      {
        path: "profile",
        name: "Profile",
        component: Profile,
      },
      {
        path: "report-anomaly",
        name: "ReportAnomaly",
        component: ReportAnomaly,
      },
    ],
  },
  {
    path: "/:pathMatch(.*)*",
    redirect: "/login",
  },
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth)
  const requiredRoles = to.matched.find((record) => record.meta.roles)?.meta.roles || []

  if (requiresAuth && !authStore.isAuthenticated) {
    next("/login")
  } else if (requiresAuth && requiredRoles.length > 0 && !requiredRoles.includes(authStore.userRole)) {
    // Rediriger vers le dashboard approprié en fonction du rôle
    if (authStore.userRole === "EMPLOYEE") {
      next("/mobile")
    } else {
      next("/dashboard")
    }
  } else {
    next()
  }
})

export default router

