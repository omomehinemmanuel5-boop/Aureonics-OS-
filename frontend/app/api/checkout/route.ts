import { NextRequest, NextResponse } from 'next/server';

const USD_PRICES: Record<'pro' | 'enterprise', number> = {
  pro: 15,
  enterprise: 49,
};

type Plan = keyof typeof USD_PRICES;

function buildInvoiceId(plan: Plan): string {
  const stamp = Date.now().toString(36).toUpperCase();
  return `LEX-${plan.toUpperCase()}-${stamp}`;
}

function buildManualInstructions(plan: Plan, amountUsd: number) {
  const paymentEmail = process.env.SALES_CONTACT_EMAIL || 'sales@lexaureon.ai';
  const termsDays = Number(process.env.MANUAL_INVOICE_TERMS_DAYS || '7');
  const due = new Date(Date.now() + termsDays * 24 * 60 * 60 * 1000).toISOString();

  return {
    checkout_mode: 'manual_invoice' as const,
    amount_usd: amountUsd,
    currency: 'USD' as const,
    due_date: due,
    payment_terms_days: termsDays,
    next_action: 'Email sales to receive a payable invoice (bank transfer, card link, or local rails).',
    payment_instructions: [
      `Send plan confirmation to ${paymentEmail}.`,
      'You will receive a payable invoice with bank transfer details and optional card payment link.',
      'Access is activated after payment confirmation.',
    ],
  };
}

export async function POST(request: NextRequest) {
  try {
    const { plan, buyerEmail, companyName } = (await request.json()) as {
      plan?: string;
      buyerEmail?: string;
      companyName?: string;
    };

    if (!plan || !(plan in USD_PRICES)) {
      return NextResponse.json({ error: 'Invalid plan requested' }, { status: 400 });
    }

    const typedPlan = plan as Plan;
    const invoiceId = buildInvoiceId(typedPlan);

    return NextResponse.json({
      invoice_id: invoiceId,
      plan: typedPlan,
      buyer_email: buyerEmail ?? null,
      company_name: companyName ?? null,
      ...buildManualInstructions(typedPlan, USD_PRICES[typedPlan]),
    });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Checkout request failed unexpectedly' },
      { status: 500 },
    );
  }
}
