import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  // 获取当前路径
  const path = request.nextUrl.pathname

  // 定义公开路径（不需要登录就能访问的路径）
  const publicPaths = ['/login', '/register', '/reset-password']

  // 如果当前路径是公开路径，直接放行
  if (publicPaths.includes(path)) {
    return NextResponse.next()
  }

  // 检查是否有登录凭证（access_token cookie）
  const isAuthenticated = request.cookies.has('access_token')
  const isGuest = request.cookies.has('guest_mode')

  // 如果既没有登录凭证也不是游客模式，重定向到登录页面
  if (!isAuthenticated && !isGuest) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('from', path)
    return NextResponse.redirect(loginUrl)
  }

  return NextResponse.next()
}

// 配置中间件匹配的路径
export const config = {
  matcher: [
    /*
     * 匹配所有路径除了：
     * /api (API routes)
     * /_next (Next.js internals)
     * /_static (static files)
     * /favicon.ico, /sitemap.xml (static files)
     */
    '/((?!api|_next|_static|favicon.ico|sitemap.xml).*)',
  ],
} 