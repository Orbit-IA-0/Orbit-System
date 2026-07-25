/**
 * Middleware de rota do Next.js.
 * A validacao real do token acontece no backend (JWT); aqui fazemos apenas
 * uma verificacao leve de presenca de cookie/local storage nao e possivel
 * em middleware de edge, entao a protecao efetiva das paginas ocorre no
 * client-side (orbitApi.me()) redirecionando para /login quando necessario.
 * Este middleware cuida apenas do cabecalho de seguranca padrao.
 */
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const response = NextResponse.next();
  response.headers.set("X-Frame-Options", "DENY");
  response.headers.set("X-Content-Type-Options", "nosniff");
  return response;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
