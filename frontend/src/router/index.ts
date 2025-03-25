import { createRouter, createWebHistory, RouteRecordRaw } from "vue-router"
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
import OrganizationDetail from "@/views/dashboard/OrganizationDetail.vue"
import Sites from "@/views/dashboard/Sites.vue"
import Timesheets from "@/views/dashboard/Timesheets.vue"
import Anomalies from "@/views/dashboard/Anomalies.vue"
import Reports from "@/views/dashboard/Reports.vue"
import Settings from "@/views/dashboard/Settings.vue"
import AdminUsers from "@/views/dashboard/admin/Users.vue"

// Views - Mobile (Employee)
import MobileDashboard from "@/views/mobile/MobileDashboard.vue"
import Scan from "@/views/mobile/Scan.vue"
import History from "@/views/mobile/History.vue"
import Profile from "@/views/mobile/Profile.vue"
import ReportAnomaly from "@/views/mobile/ReportAnomaly.vue"

interface RouteMeta {
  requiresAuth?: boolean;
  roles?: string[];
}

const routes: RouteRecordRaw[] = [
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
      // Routes Super Admin
      {
        path: "admin/users",
        name: "Users",
        component: AdminUsers,
        meta: { roles: ["SUPER_ADMIN", "MANAGER"] },
      },
      {
        path: "organizations/:id",
        name: "OrganizationDetail",
        component: OrganizationDetail,
        meta: { roles: ["SUPER_ADMIN"] },
      },
      // Routes communes
      {
        path: "sites",
        name: "Sites",
        component: Sites,
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
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth)
  const requiredRoles = to.matched.find((record) => record.meta.roles)?.meta.roles || []

  // Si la route nécessite une authentification
  if (requiresAuth) {
    // Vérifier si l'utilisateur est déjà authentifié
    if (!authStore.isAuthenticated) {
      console.log("Route protégée, redirection vers login")
      next("/login")
      return
    }

    // Si l'utilisateur est authentifié mais qu'on n'a pas son profil
    if (!authStore.user) {
      console.log("Token présent mais pas de profil, tentative de récupération")
      try {
        await authStore.initAuth()
      } catch (error) {
        console.error("Échec de l'initialisation de l'auth:", error)
        next("/login")
        return
      }
    }

    // Vérifier les rôles requis
    if (requiredRoles.length > 0 && !requiredRoles.includes(authStore.userRole)) {
      console.log("Accès refusé - rôle incorrect:", authStore.userRole)
      // Rediriger vers le dashboard approprié en fonction du rôle
      if (authStore.userRole === "EMPLOYEE") {
        next("/mobile")
      } else {
        next("/dashboard")
      }
      return
    }
  }

  // Si l'utilisateur est déjà authentifié et essaie d'accéder à login
  if (to.path === "/login" && authStore.isAuthenticated) {
    console.log("Utilisateur déjà connecté, redirection vers le dashboard")
    if (authStore.isEmployee) {
      next("/mobile")
    } else {
      next("/dashboard")
    }
    return
  }

  next()
})

export default router

