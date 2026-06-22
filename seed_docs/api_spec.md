# ShopFlow — REST API Specification

All endpoints are prefixed with `/api/v1`. Requests and responses use JSON.
Authentication uses a bearer token in the `Authorization` header.

## Products

### GET /products
Returns a paginated list of products. Query parameters: `category`, `page`,
`page_size` (default 20, max 100).

### GET /products/{id}
Returns a single product by id. Responds `404` if the product does not exist.

## Cart

### POST /cart/items
Adds a line item to the current customer's cart. Body: `{ "product_id", "quantity" }`.
Responds `409` if the requested quantity exceeds available inventory.

### DELETE /cart/items/{product_id}
Removes a line item from the cart.

## Orders

### POST /orders
Creates an order from the current cart (checkout). Body: `{ "shipping_address", "payment_method" }`.
Responds `402` if payment capture fails.

### GET /orders/{id}
Returns a single order, including its line items and current status.

### POST /orders/{id}/cancel
Cancels an order. Only orders in `pending` or `paid` status can be cancelled;
cancelling a `shipped` order responds `409`.
