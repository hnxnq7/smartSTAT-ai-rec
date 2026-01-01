# smartSTAT - AI Recommendations Demo

A medication management dashboard with AI-powered ordering recommendations.

## Features

- **Intelligent Recommendations**: Calculates optimal order quantities and timing based on:
  - Historical usage patterns (daily usage rate)
  - Expiration dates and batch-level inventory
  - User preferences (surplus days, minimum shelf life, lead time)
  - Service level targets

- **Risk Management**: 
  - Identifies medications at risk of stockout
  - Flags medications approaching expiration
  - Projects potential waste from expiring inventory

- **Interactive Dashboard**:
  - Filter by cart, department, planning horizon, and risk type
  - Summary cards showing key metrics
  - Detailed table with all recommendations
  - Side panel with detailed explanations and preference editing

- **Real-time Updates**: Adjust preferences and see recommendations update instantly

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Run the development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build for Production

```bash
npm run build
npm start
```

## Project Structure

```
smartSTAT/
├── app/                    # Next.js app directory
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Main page
│   └── globals.css        # Global styles
├── components/            # React components
│   ├── ui/               # Reusable UI components
│   ├── AIRecommendations.tsx
│   ├── FilterBar.tsx
│   ├── SummaryCards.tsx
│   ├── RecommendationsTable.tsx
│   ├── RecommendationDetails.tsx
│   └── PreferencesEditor.tsx
├── lib/                  # Business logic
│   ├── data.ts          # Synthetic data generation
│   └── recommendations.ts # Recommendation calculation engine
├── types/               # TypeScript type definitions
│   └── inventory.ts
└── package.json
```

## How It Works

### Recommendation Algorithm

1. **Usage Analysis**: Calculates daily usage rate (λ) from historical usage events over the last 45 days
2. **Demand Forecasting**: Projects demand over the planning horizon (7/14/30 days)
3. **Safety Stock**: Calculates safety stock based on service level and lead time variability
4. **Usable Inventory**: Filters batches by expiration date, considering minimum remaining shelf life
5. **Order Calculation**: 
   - Target Stock = Forecast Demand + Safety Stock + Preferred Surplus
   - Recommended Order = Target Stock - Usable Stock

### Key Metrics

- **Daily Usage Rate (λ)**: Average units consumed per day
- **Forecast Demand**: Expected consumption over planning horizon
- **Safety Stock**: Buffer stock to handle variability (based on service level)
- **Usable Stock**: Current inventory that won't expire before use
- **Recommended Order Quantity**: Amount to order to reach target stock level

## Customization

### Adjusting Preferences

Click "Details" on any recommendation to:
- Change surplus days (0-14)
- Adjust minimum remaining shelf life (0-90 days)
- Modify lead time
- Update service level (90%, 95%, 99%)

Changes update recommendations in real-time.

### Synthetic Data

The demo uses synthetic data generated in `lib/data.ts`. To customize:
- Modify medication names in `MEDICATION_NAMES`
- Adjust departments in `DEPARTMENTS`
- Change usage patterns, batch quantities, or expiration dates

## Tech Stack

- **Next.js 14**: React framework
- **TypeScript**: Type safety
- **Tailwind CSS**: Styling
- **date-fns**: Date manipulation
- **lucide-react**: Icons

## License

This is a demo project for demonstration purposes.







