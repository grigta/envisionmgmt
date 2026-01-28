# OmniSupport 💬

AI-powered customer support chat widget for businesses.

## Features

- 🤖 AI-powered responses using Claude/GPT
- 💬 Embeddable chat widget
- 🎨 Customizable themes (light/dark)
- 📱 Mobile-friendly responsive design
- 🔌 Easy integration (single script tag)

## Installation

Add the widget to your website:

```html
<script src="https://omnisupport.attention.dev/widget.js"></script>
<script>
  OmniSupport.init({
    apiKey: 'YOUR_API_KEY',
    theme: 'light', // or 'dark'
    position: 'bottom-right'
  });
</script>
```

## Project Structure

```
omnisupport/
├── backend/      # API server
├── frontend/     # Admin dashboard
├── widget/       # Embeddable chat widget
└── wireframes/   # Design mockups
```

## Development

```bash
# Backend
cd backend && npm install && npm run dev

# Frontend
cd frontend && npm install && npm run dev

# Widget
cd widget && npm install && npm run build
```

## Tech Stack

- **Backend**: Node.js, Express, SQLite
- **Frontend**: React, Tailwind CSS
- **Widget**: Vanilla JS, minimal footprint
- **AI**: Claude API / OpenAI API

## License

MIT © Attention.dev
