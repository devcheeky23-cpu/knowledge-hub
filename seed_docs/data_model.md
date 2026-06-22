# ShopFlow — Data Model (ERD Description)

This document describes the core entities and their relationships.

## Customer

A Customer has an id, email, and hashed password. A Customer has one Cart and
many Orders.

## Product

A Product has an id, name, description, price, inventory count, and a category.
A Product appears in many Cart Items and many Order Items.

## Cart

A Cart belongs to exactly one Customer and contains many Cart Items. A Cart Item
references one Product and a quantity.

## Order

An Order belongs to one Customer and contains many Order Items. An Order has a
status, a shipping address, a total amount, and a created timestamp. Each Order
Item captures the product, quantity, and the unit price at the time of purchase
(so historical orders are unaffected by later price changes).

## Payment

A Payment belongs to one Order and records the amount, the payment method, and
the capture status. An Order has exactly one Payment.
