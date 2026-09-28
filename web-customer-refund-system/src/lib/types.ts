// Shapes returned by the FastAPI backend - kept in sync with the Pydantic
// schemas in api_customer_refund_system/schemas/. There's no code generation
// wiring the two together; if the backend response shape changes, these need
// updating by hand.

export type Customer = {
  id: string;
  name: string;
  email: string;
};

export type OrderItem = {
  id: string;
  sku: string;
  description: string | null;
  price: number;
  quantity: number;
};

export type OrderStatus = "delivered" | "in_transit" | "cancelled";

export type Order = {
  id: string;
  order_date: string;
  total_amount: number;
  status: OrderStatus;
  is_final_sale: boolean;
  items: OrderItem[];
};

export type CustomerOrders = {
  customer: Customer & { signup_date: string | null; risk_flag: boolean };
  orders: Order[];
};

export type RefundDecisionStatus = "approved" | "denied" | "escalated" | "pending";

export type RefundRequestResult = {
  id: string;
  status: RefundDecisionStatus;
  reasoning: string;
  policy_version: number;
  flags: string[];
  created_at: string;
};

export type RefundRequestListItem = {
  id: string;
  customer_id: string;
  customer_name: string;
  order_id: string;
  message: string;
  requested_amount: number | null;
  status: RefundDecisionStatus;
  reasoning: string | null;
  flags: string[];
  created_at: string;
  resolved_at: string | null;
};
