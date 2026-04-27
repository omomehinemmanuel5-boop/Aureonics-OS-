import { NextRequest, NextResponse } from 'next/server';
import Stripe from 'stripe';

const stripeSecret = process.env.STRIPE_SECRET_KEY;

const priceMap: Record<string, string | undefined> = {
  pro: process.env.STRIPE_PRICE_ID_PRO,
  enterprise: process.env.STRIPE_PRICE_ID_ENTERPRISE
};

export async function POST(request: NextRequest) {
  try {
    if (!stripeSecret) {
      return NextResponse.json({ error: 'Missing STRIPE_SECRET_KEY' }, { status: 500 });
    }

    const { plan } = (await request.json()) as { plan?: string };
    if (!plan || !priceMap[plan]) {
      return NextResponse.json({ error: 'Invalid plan requested' }, { status: 400 });
    }

    const stripe = new Stripe(stripeSecret);
    const origin = request.nextUrl.origin;
    const session = await stripe.checkout.sessions.create({
      mode: 'subscription',
      line_items: [{ price: priceMap[plan], quantity: 1 }],
      success_url: `${origin}/app`,
      cancel_url: `${origin}/pricing`
    });

    return NextResponse.json({ url: session.url });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Checkout failed unexpectedly' },
      { status: 500 }
    );
  }
}
