# ShopFlow — Product Requirements

## Overview

ShopFlow is a mock e-commerce platform used as the seed corpus for the Knowledge
Hub demo. It lets customers browse a product catalog, add items to a cart, check
out, and manage their orders.

## Catalog

Products are organised into categories. Each product has a name, description,
price in USD, and an inventory count. Products with zero inventory are shown as
"Out of stock" and cannot be added to a cart.

## Cart

A cart belongs to a single customer and holds line items. Each line item
references a product and a quantity. The cart subtotal is the sum of line item
prices. Carts are persisted for 30 days of inactivity before being cleared.

## Checkout

Checkout converts a cart into an order. The customer confirms a shipping address
and a payment method. Payment is captured at checkout; if payment fails, the
order is not created and the cart is preserved.

## Orders

An order has a status: `pending`, `paid`, `shipped`, `delivered`, or `cancelled`.
Customers can view their order history and track shipment status from the orders
page.
