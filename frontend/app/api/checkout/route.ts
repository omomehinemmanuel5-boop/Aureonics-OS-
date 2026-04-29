import { NextRequest, NextResponse } from 'next/server';

const USD_PRICES: Record<'pro' | 'enterprise', number> = {
  pro: 15,
  enterprise: 49,
};

type Plan = keyof typeof USD_PRICES;

type CheckoutRequest = {
  plan?: string;
  buyerEmail?: string;
  companyName?: string;
  seats?: number;
  notes?: string;
};

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function buildInvoiceId(plan: Plan): string {
  const stamp = Date.now().toString(36).toUpperCase();
  return `LEX-${plan.toUpperCase()}-${stamp}`;
}

function buildManualInstructions(input: {
  plan: Plan;
  amountUsd: number;
  buyerEmail: string;
  companyName: string;
  seats: number;
  notes?: string;
  invoiceId: string;
}) {
  const paymentEmail = process.env.SALES_CONTACT_EMAIL || 'Lexaureon@gmail.com';
  const salesPhone = process.env.SALES_PHONE_E164 || '+2349135275035';
  const termsDays = Number(process.env.MANUAL_INVOICE_TERMS_DAYS || '7');
  const due = new Date(Date.now() + termsDays * 24 * 60 * 60 * 1000).toISOString();
  const totalUsd = input.amountUsd * input.seats;

  const subject = `Lex Aureon Invoice Request ${input.invoiceId}`;
  const emailBody = [
    `Invoice ID: ${input.invoiceId}`,
    `Plan: ${input.plan}`,
    `Company: ${input.companyName}`,
    `Buyer Email: ${input.buyerEmail}`,
    `Seats: ${input.seats}`,
    `Amount USD: ${totalUsd}`,
    `Notes: ${input.notes ?? 'N/A'}`,
  ].join('\n');

  const waText = encodeURIComponent(
    `Invoice Request ${input.invoiceId} | plan=${input.plan} | company=${input.companyName} | email=${input.buyerEmail} | seats=${input.seats} | total_usd=${totalUsd}`,
  );

  return {
    checkout_mode: 'manual_invoice' as const,
    unit_amount_usd: input.amountUsd,
    total_amount_usd: totalUsd,
    currency: 'USD' as const,
    due_date: due,
    payment_terms_days: termsDays,
    next_action: 'Send invoice request through email or WhatsApp now to receive payable invoice within 1 business day.',
    payment_instructions: [
      `Email ${paymentEmail} with invoice id ${input.invoiceId}.`,
      'Sales will issue a payable invoice with bank transfer details and card alternatives.',
      'Provisioning starts immediately after payment confirmation.',
    ],
    actions: {
      mailto_url: `mailto:${paymentEmail}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(emailBody)}`,
      whatsapp_url: `https://wa.me/${salesPhone.replace('+', '')}?text=${waText}`,
    },
  };
}

function validate(body: CheckoutRequest): { ok: true; plan: Plan; buyerEmail: string; companyName: string; seats: number; notes?: string } | { ok: false; error: string } {
  if (!body.plan || !(body.plan in USD_PRICES)) return { ok: false, error: 'Invalid plan requested' };
  if (!body.buyerEmail || !EMAIL_RE.test(body.buyerEmail)) return { ok: false, error: 'Valid buyer email is required' };
  if (!body.companyName || body.companyName.trim().length < 2) return { ok: false, error: 'Valid company name is required' };
  const seats = body.seats ?? 1;
  if (!Number.isInteger(seats) || seats < 1 || seats > 1000) return { ok: false, error: 'Seats must be an integer between 1 and 1000' };

  return {
    ok: true,
    plan: body.plan as Plan,
    buyerEmail: body.buyerEmail.trim(),
    companyName: body.companyName.trim(),
    seats,
    notes: body.notes?.trim() || undefined,
  };
}

export async function POST(request: NextRequest) {
  try {
    const body = (await request.json()) as CheckoutRequest;
    const checked = validate(body);
    if (!checked.ok) return NextResponse.json({ error: checked.error }, { status: 400 });

    const invoiceId = buildInvoiceId(checked.plan);

    return NextResponse.json({
      invoice_id: invoiceId,
      plan: checked.plan,
      buyer_email: checked.buyerEmail,
      company_name: checked.companyName,
      seats: checked.seats,
      notes: checked.notes ?? null,
      ...buildManualInstructions({
        plan: checked.plan,
        amountUsd: USD_PRICES[checked.plan],
        buyerEmail: checked.buyerEmail,
        companyName: checked.companyName,
        seats: checked.seats,
        notes: checked.notes,
        invoiceId,
      }),
    });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Checkout request failed unexpectedly' },
      { status: 500 },
    );
  }
}
