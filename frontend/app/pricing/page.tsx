import { CheckoutButton } from '@/components/CheckoutButton';

const plans = [
  { name: 'FREE', price: '$0', bullets: ['10 runs/day', 'Basic transformation'] },
  { name: 'PRO', price: '$15/mo', bullets: ['500 runs/day', 'Faster processing', 'Invoice-based checkout'] },
  { name: 'ENTERPRISE', price: '$49+/mo', bullets: ['API access', 'Priority queue', 'Procurement-ready invoicing'] }
] as const;

export default function PricingPage() {
  return (
    <section className="section-pad">
      <div className="container-shell">
        <h1 className="text-3xl font-semibold tracking-tight">Pricing (No Stripe required)</h1>
        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {plans.map((plan) => (
            <article key={plan.name} className="rounded-xl2 border border-slate-200 bg-white p-6 shadow-card">
              <h2 className="text-xl font-semibold">{plan.name}</h2>
              <p className="mt-2 text-2xl font-bold">{plan.price}</p>
              <ul className="mt-4 space-y-2 text-sm text-slate-600">
                {plan.bullets.map((bullet) => (
                  <li key={bullet}>• {bullet}</li>
                ))}
              </ul>
              {plan.name === 'PRO' ? <CheckoutButton plan="pro" /> : null}
              {plan.name === 'ENTERPRISE' ? <CheckoutButton plan="enterprise" /> : null}
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
