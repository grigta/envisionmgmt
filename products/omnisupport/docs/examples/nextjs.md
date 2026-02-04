# OmniSupport + Next.js

Интеграция чат-виджета в Next.js приложение (App Router & Pages Router).

---

## Установка

```bash
npm install @omnisupport/react
# или
yarn add @omnisupport/react
```

---

## App Router (Next.js 13+)

### Провайдер

```tsx
// app/providers.tsx
'use client';

import { OmniSupportProvider } from '@omnisupport/react';

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <OmniSupportProvider apiKey={process.env.NEXT_PUBLIC_OMNISUPPORT_KEY!}>
      {children}
    </OmniSupportProvider>
  );
}
```

### Layout

```tsx
// app/layout.tsx
import { Providers } from './providers';
import { OmniSupportWidget } from './omni-widget';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru">
      <body>
        <Providers>
          {children}
          <OmniSupportWidget />
        </Providers>
      </body>
    </html>
  );
}
```

### Client Component для виджета

```tsx
// app/omni-widget.tsx
'use client';

import { ChatWidget } from '@omnisupport/react';

export function OmniSupportWidget() {
  return <ChatWidget />;
}
```

### Идентификация пользователя

```tsx
// app/components/user-identify.tsx
'use client';

import { useEffect } from 'react';
import { useOmniSupport } from '@omnisupport/react';
import { useSession } from 'next-auth/react';

export function UserIdentify() {
  const { data: session } = useSession();
  const { identify } = useOmniSupport();

  useEffect(() => {
    if (session?.user) {
      identify({
        userId: session.user.id,
        email: session.user.email!,
        name: session.user.name!
      });
    }
  }, [session, identify]);

  return null;
}
```

---

## Pages Router

### _app.tsx

```tsx
// pages/_app.tsx
import type { AppProps } from 'next/app';
import { OmniSupportProvider, ChatWidget } from '@omnisupport/react';

export default function App({ Component, pageProps }: AppProps) {
  return (
    <OmniSupportProvider apiKey={process.env.NEXT_PUBLIC_OMNISUPPORT_KEY!}>
      <Component {...pageProps} />
      <ChatWidget />
    </OmniSupportProvider>
  );
}
```

### Динамическая загрузка (ленивая)

```tsx
// pages/_app.tsx
import dynamic from 'next/dynamic';
import { OmniSupportProvider } from '@omnisupport/react';

const ChatWidget = dynamic(
  () => import('@omnisupport/react').then((mod) => mod.ChatWidget),
  { ssr: false }
);

export default function App({ Component, pageProps }) {
  return (
    <OmniSupportProvider apiKey={process.env.NEXT_PUBLIC_OMNISUPPORT_KEY}>
      <Component {...pageProps} />
      <ChatWidget />
    </OmniSupportProvider>
  );
}
```

---

## Server Components + Streaming

Виджет — клиентский компонент, но данные можно получать на сервере.

```tsx
// app/support/page.tsx
import { Suspense } from 'react';
import { SupportChat } from './support-chat';
import { getServerSession } from 'next-auth';

async function getUserData() {
  const session = await getServerSession();
  return session?.user;
}

export default async function SupportPage() {
  const user = await getUserData();

  return (
    <div>
      <h1>Поддержка</h1>
      <Suspense fallback={<div>Загрузка...</div>}>
        <SupportChat user={user} />
      </Suspense>
    </div>
  );
}
```

```tsx
// app/support/support-chat.tsx
'use client';

import { useEffect } from 'react';
import { useOmniSupport } from '@omnisupport/react';

export function SupportChat({ user }: { user?: { id: string; email: string; name: string } }) {
  const { open, identify } = useOmniSupport();

  useEffect(() => {
    if (user) {
      identify({
        userId: user.id,
        email: user.email,
        name: user.name
      });
    }
    // Автоматически открываем на странице поддержки
    open();
  }, [user, identify, open]);

  return (
    <div className="p-4 bg-gray-100 rounded">
      <p>Чат открыт справа →</p>
    </div>
  );
}
```

---

## Middleware и Edge

```typescript
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const response = NextResponse.next();
  
  // CSP для виджета
  response.headers.set(
    'Content-Security-Policy',
    "script-src 'self' https://widget.omnisupport.ru; frame-src https://widget.omnisupport.ru;"
  );
  
  return response;
}
```

---

## Environment Variables

```bash
# .env.local
NEXT_PUBLIC_OMNISUPPORT_KEY=pk_live_your_api_key
```

**Важно:** Используйте `NEXT_PUBLIC_` префикс для клиентских переменных.

---

## Полный пример (App Router)

```
app/
├── layout.tsx
├── providers.tsx
├── omni-widget.tsx
├── components/
│   └── user-identify.tsx
└── page.tsx
```

```tsx
// app/layout.tsx
import { Inter } from 'next/font/google';
import { Providers } from './providers';
import { OmniSupportWidget } from './omni-widget';
import { UserIdentify } from './components/user-identify';
import './globals.css';

const inter = Inter({ subsets: ['latin', 'cyrillic'] });

export const metadata = {
  title: 'My App',
  description: 'App with OmniSupport'
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru">
      <body className={inter.className}>
        <Providers>
          <UserIdentify />
          <main>{children}</main>
          <OmniSupportWidget />
        </Providers>
      </body>
    </html>
  );
}
```

```tsx
// app/providers.tsx
'use client';

import { SessionProvider } from 'next-auth/react';
import { OmniSupportProvider } from '@omnisupport/react';

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <SessionProvider>
      <OmniSupportProvider 
        apiKey={process.env.NEXT_PUBLIC_OMNISUPPORT_KEY!}
        options={{
          theme: 'auto',
          position: 'bottom-right'
        }}
      >
        {children}
      </OmniSupportProvider>
    </SessionProvider>
  );
}
```

---

## API Routes

Серверный доступ к OmniSupport API.

```typescript
// app/api/support/conversations/route.ts
import { NextResponse } from 'next/server';

const OMNISUPPORT_SECRET = process.env.OMNISUPPORT_SECRET_KEY;

export async function GET() {
  const res = await fetch('https://api.omnisupport.ru/api/v1/conversations', {
    headers: {
      Authorization: `Bearer ${OMNISUPPORT_SECRET}`
    }
  });
  
  const data = await res.json();
  return NextResponse.json(data);
}
```

---

## Vercel Deploy

```json
// vercel.json
{
  "env": {
    "NEXT_PUBLIC_OMNISUPPORT_KEY": "@omnisupport-key"
  }
}
```

```bash
vercel env add NEXT_PUBLIC_OMNISUPPORT_KEY
```

---

## Ресурсы

- [Полная документация](https://docs.omnisupport.attention.dev/nextjs)
- [GitHub репозиторий](https://github.com/omnisupport/sdk-react)
- [Шаблон на Vercel](https://vercel.com/templates/next.js/omnisupport)
