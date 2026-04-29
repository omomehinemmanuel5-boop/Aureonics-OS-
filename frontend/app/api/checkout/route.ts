import { NextRequest, NextResponse } from 'next/server';

const USD_PRICES: Record<'pro' | 'enterprise', number> = {
  pro: 15,
  enterprise: 49,
};

type Plan = keyof typeof USD_PRICES;

type CheckoutBody = {
  plan?: string;
  buyerEmail?: string;
  companyName?: string;
  seats?: number;
};

function buildInvoiceId(plan: Plan): string {
  const stamp = Date.now().toString(36).toUpperCase();
  return `LEX-${plan.toUpperCase()}-${stamp}`;
}

function normalizeString(value: string | undefined): string {
  return (value ?? '').trim();
}

function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function buildManualInstructions(amountUsd: number) {
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
      `Send this request to ${paymentEmail}.`,
      'You will receive a payable invoice with bank transfer details and optional card payment link.',
      'Access is activated after payment confirmation.',
    ],
    sales_contact_email: paymentEmail,
  };
}

export async function POST(request: NextRequest) {
  try {
    const { plan, buyerEmail, companyName, seats } = (await request.json()) as CheckoutBody;

    if (!plan || !(plan in USD_PRICES)) {
      return NextResponse.json({ error: 'Invalid plan requested' }, { status: 400 });
    }

    const email = normalizeString(buyerEmail);
    const company = normalizeString(companyName);
    const seatCount = typeof seats === 'number' ? seats : 1;

    if (!isValidEmail(email)) {
      return NextResponse.json({ error: 'Valid buyer email is required' }, { status: 400 });
    }

    if (company.length < 2) {
      return NextResponse.json({ error: 'Company name is required' }, { status: 400 });
    }

    if (!Number.isInteger(seatCount) || seatCount < 1 || seatCount > 1000) {
      return NextResponse.json({ error: 'Seats must be an integer between 1 and 1000' }, { status: 400 });
    }

    const typedPlan = plan as Plan;
    const invoiceId = buildInvoiceId(typedPlan);
    const subtotal = USD_PRICES[typedPlan] * seatCount;
    const payload = buildManualInstructions(subtotal);

    const emailTemplate = [
      `Subject: Lex Aureon ${typedPlan.toUpperCase()} Invoice Request (${invoiceId})`,
      '',
      `Plan: ${typedPlan}`,
      `Seats: ${seatCount}`,
      `Company: ${company}`,
      `Buyer Email: ${email}`,
      `Amount (USD): ${subtotal}`,
      `Invoice ID: ${invoiceId}`,
      '',
      'Please issue payable invoice and activation timeline.',
    ].join('\n');

    return NextResponse.json({
      invoice_id: invoiceId,
      plan: typedPlan,
      buyer_email: email,
      company_name: company,
      seats: seatCount,
      unit_price_usd: USD_PRICES[typedPlan],
      ...payload,
      email_template: emailTemplate,
    });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Checkout request failed unexpectedly' },
      { status: 500 },
    );
  }
}
