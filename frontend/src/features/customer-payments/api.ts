import {
  apiRequest,
} from "@/lib/api/client";

import type {
  CustomerPaymentData,
  CustomerPaymentDetail,
  CustomerPaymentListData,
  CustomerPaymentListParameters,
} from "@/features/customer-payments/types";

type QueryValue =
  | string
  | number
  | boolean
  | undefined;

function buildQuery(
  parameters: Record<
    string,
    QueryValue
  >,
): string {
  const searchParameters =
    new URLSearchParams();

  for (
    const [
      key,
      value,
    ]
    of Object.entries(
      parameters,
    )
  ) {
    if (
      value === undefined
      ||
      value === ""
    ) {
      continue;
    }

    searchParameters.set(
      key,
      String(
        value,
      ),
    );
  }

  const query =
    searchParameters.toString();

  return query
    ? `?${query}`
    : "";
}

export async function listCustomerPayments(
  parameters:
    CustomerPaymentListParameters = {},
): Promise<CustomerPaymentListData> {
  const response =
    await apiRequest<
      CustomerPaymentListData
    >(
      (
        "/customer-payments/"
        +
        buildQuery({
          page:
            parameters.page,
          page_size:
            parameters.page_size,
          customer_id:
            parameters.customer_id,
          invoice_id:
            parameters.invoice_id,
          bank_account_id:
            parameters.bank_account_id,
          payment_method:
            parameters.payment_method,
          search:
            parameters.search,
          sort:
            parameters.sort,
        })
      ),
    );

  return response.data;
}

export async function getCustomerPayment(
  paymentId: string,
): Promise<CustomerPaymentDetail> {
  const response =
    await apiRequest<
      CustomerPaymentData
    >(
      (
        `/customer-payments/`
        +
        `${paymentId}/`
      ),
    );

  return response.data.payment;
}