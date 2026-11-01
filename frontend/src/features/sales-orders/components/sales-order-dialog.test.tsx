import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";

import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import SalesOrderDialog
  from "@/features/sales-orders/components/sales-order-dialog";

const mockUseCustomerList =
  vi.fn();

const mockUseWarehouseList =
  vi.fn();

const mockUseSalesOrder =
  vi.fn();

const mockCreateMutateAsync =
  vi.fn();

const mockUpdateMutateAsync =
  vi.fn();

const mockCreateReset =
  vi.fn();

const mockUpdateReset =
  vi.fn();

vi.mock(
  "@/features/customers/hooks",
  () => ({
    useCustomerList: (
      ...args: unknown[]
    ) =>
      mockUseCustomerList(
        ...args,
      ),
  }),
);

vi.mock(
  "@/features/warehouses/hooks",
  () => ({
    useWarehouseList: (
      ...args: unknown[]
    ) =>
      mockUseWarehouseList(
        ...args,
      ),
  }),
);

vi.mock(
  "@/features/sales-orders/hooks",
  () => ({
    useSalesOrder: (
      ...args: unknown[]
    ) =>
      mockUseSalesOrder(
        ...args,
      ),

    useCreateSalesOrder: () => ({
      mutateAsync:
        mockCreateMutateAsync,
      reset:
        mockCreateReset,
      isPending: false,
      error: null,
    }),

    useUpdateSalesOrder: () => ({
      mutateAsync:
        mockUpdateMutateAsync,
      reset:
        mockUpdateReset,
      isPending: false,
      error: null,
    }),
  }),
);

vi.mock(
  "@/features/customers/components/customer-dialog",
  () => ({
    default: ({
      open,
      onCreated,
    }: {
      open: boolean;
      onCreated: (
        customer: {
          id: string;
          code: string;
          name: string;
        },
      ) => void;
    }) =>
      open ? (
        <div data-testid="customer-dialog">
          <button
            type="button"
            onClick={() => {
              onCreated({
                id: "customer-created",
                code: "CUS-NEW",
                name: "New Customer",
              });
            }}
          >
            Complete customer creation
          </button>
        </div>
      ) : null,
  }),
);

vi.mock(
  "@/features/products/components/product-dialog",
  () => ({
    default: ({
      open,
      onCreated,
    }: {
      open: boolean;
      onCreated: (
        product: {
          id: string;
          sku: string;
          name: string;
          selling_price: string;
        },
      ) => void;
    }) =>
      open ? (
        <div data-testid="product-dialog">
          <button
            type="button"
            onClick={() => {
              onCreated({
                id: "product-created",
                sku: "SKU-NEW",
                name: "New Product",
                selling_price:
                  "250.00",
              });
            }}
          >
            Complete product creation
          </button>
        </div>
      ) : null,
  }),
);

vi.mock(
  "@/features/sales-orders/components/sales-order-product-search",
  () => ({
    default: ({
      value,
      canCreateProduct,
      onSelect,
      onClear,
      onCreate,
    }: {
      value: string;
      canCreateProduct: boolean;
      onSelect: (
        product: {
          id: string;
          sku: string;
          name: string;
          selling_price: string;
        },
      ) => void;
      onClear: () => void;
      onCreate: () => void;
    }) => (
      <div data-testid="product-search">
        <span>
          {value || "No product selected"}
        </span>

        <button
        type="button"
        aria-label="Select existing product"
        onClick={() => {
            onSelect({
            id: "product-existing",
            sku: "SKU-001",
            name: "Existing Product",
            selling_price:
                "125.00",
            });
        }}
        >
        Select existing product
        </button>

        <button
          type="button"
          onClick={onClear}
        >
          Clear product
        </button>

        {canCreateProduct ? (
          <button
            type="button"
            onClick={onCreate}
          >
            Create product
          </button>
        ) : null}
      </div>
    ),
  }),
);

const customer = {
  id: "customer-1",
  code: "CUS-001",
  name: "Test Customer",
  phone: "9999999999",
  email: "customer@example.com",
};

const warehouse = {
  id: "warehouse-1",
  code: "WH-001",
  name: "Main Warehouse",
};

async function renderDialog({
  canCreateCustomer = true,
  canCreateProduct = true,
}: {
  canCreateCustomer?: boolean;
  canCreateProduct?: boolean;
} = {}) {
  const onClose =
    vi.fn();

  await act(async () => { render(
    <SalesOrderDialog
      open
      salesOrderId={null}
      canCreateCustomer={
        canCreateCustomer
      }
      canCreateProduct={
        canCreateProduct
      }
      onClose={onClose}
    />,
  ); });

  return {
    onClose,
  };
}

describe(
  "SalesOrderDialog",
  () => {
    beforeEach(() => {
      vi.clearAllMocks();

      mockUseSalesOrder
        .mockReturnValue({
          data: undefined,
          isPending: false,
          isError: false,
          error: null,
          refetch: vi.fn(),
        });

      mockUseCustomerList
        .mockReturnValue({
          data: {
            customers: [],
          },
          isFetching: false,
          isPending: false,
        });

      mockUseWarehouseList
        .mockReturnValue({
          data: {
            warehouses: [
              warehouse,
            ],
          },
          isPending: false,
        });

      mockCreateMutateAsync
        .mockResolvedValue({
          id: "sales-order-1",
        });

      mockUpdateMutateAsync
        .mockResolvedValue({
          id: "sales-order-1",
        });
    });

    it(
      "does not search customers below three characters",
      async () => {
        await renderDialog();

        changeControl(
          screen.getByPlaceholderText(
            "Search customer name, phone, email or code",
          ),
          {
            target: {
              value: "Te",
            },
          },
        );

        expect(
          mockUseCustomerList,
        ).toHaveBeenLastCalledWith(
          {
            page: 1,
            page_size: 10,
            search: undefined,
            is_active: true,
            sort: "name",
          },
          false,
        );
      },
    );

    it(
      "searches customers after three characters",
      async () => {
        await renderDialog();

        changeControl(
          screen.getByPlaceholderText(
            "Search customer name, phone, email or code",
          ),
          {
            target: {
              value: "Test",
            },
          },
        );

        expect(
          mockUseCustomerList,
        ).toHaveBeenLastCalledWith(
          {
            page: 1,
            page_size: 10,
            search: "Test",
            is_active: true,
            sort: "name",
          },
          true,
        );
      },
    );

    it(
      "selects an existing customer",
      async () => {
        mockUseCustomerList
          .mockReturnValue({
            data: {
              customers: [
                customer,
              ],
            },
            isFetching: false,
            isPending: false,
          });

        await renderDialog();

        const input =
          screen.getByPlaceholderText(
            "Search customer name, phone, email or code",
          );

        changeControl(
          input,
          {
            target: {
              value: "Test",
            },
          },
        );

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name:
                /CUS-001.*Test Customer/i,
            },
          ),
        );

        expect(
        input,
        ).toHaveValue(
        "CUS-001 — Test Customer",
        );
      },
    );

    it(
      "opens inline customer creation when permitted",
      async () => {
        await renderDialog({
          canCreateCustomer: true,
        });

        const input =
          screen.getByPlaceholderText(
            "Search customer name, phone, email or code",
          );

        changeControl(
          input,
          {
            target: {
              value:
                "New Customer",
            },
          },
        );

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name:
                'Create "New Customer"',
            },
          ),
        );

        expect(
          screen.getByTestId(
            "customer-dialog",
          ),
        ).toBeInTheDocument();

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name:
                "Complete customer creation",
            },
          ),
        );

        expect(
        input,
        ).toHaveValue(
        "CUS-NEW — New Customer",
        );
      },
    );

    it(
      "hides inline customer creation without permission",
      async () => {
        await renderDialog({
          canCreateCustomer: false,
        });

        const input =
          screen.getByPlaceholderText(
            "Search customer name, phone, email or code",
          );

        changeControl(
          input,
          {
            target: {
              value:
                "New Customer",
            },
          },
        );

        expect(
          screen.queryByRole(
            "button",
            {
              name:
                'Create "New Customer"',
            },
          ),
        ).not.toBeInTheDocument();
      },
    );

    it(
      "selects an existing product and autofills unit price",
      async () => {
        await renderDialog();

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name:
                "Select existing product",
            },
          ),
        );

        expect(
          screen.getByText(
            /SKU-001.*Existing Product/i,
          ),
        ).toBeInTheDocument();

        const numberInputs =
          screen.getAllByRole(
            "spinbutton",
          );

        expect(
          numberInputs[1],
        ).toHaveValue(125);
      },
    );

    it(
      "creates a product inline and attaches it to the row",
      async () => {
        await renderDialog();

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name:
                "Create product",
            },
          ),
        );

        expect(
          screen.getByTestId(
            "product-dialog",
          ),
        ).toBeInTheDocument();

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name:
                "Complete product creation",
            },
          ),
        );

        expect(
          screen.getByText(
            /SKU-NEW.*New Product/i,
          ),
        ).toBeInTheDocument();

        const numberInputs =
          screen.getAllByRole(
            "spinbutton",
          );

        expect(
          numberInputs[1],
        ).toHaveValue(250);
      },
    );

    it(
      "keeps product creation hidden without permission",
      async () => {
        await renderDialog({
          canCreateProduct: false,
        });

        expect(
          screen.queryByRole(
            "button",
            {
              name:
                "Create product",
            },
          ),
        ).not.toBeInTheDocument();

        expect(
          screen.getByRole(
            "button",
            {
              name:
                "Select existing product",
            },
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "keeps product rows isolated during inline creation",
      async () => {
        await renderDialog();

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name: "Add item",
            },
          ),
        );

        const existingButtons =
          screen.getAllByRole(
            "button",
            {
              name:
                "Select existing product",
            },
          );

        fireEvent.click(
          existingButtons[0],
        );

        const createButtons =
          screen.getAllByRole(
            "button",
            {
              name:
                "Create product",
            },
          );

        fireEvent.click(
          createButtons[1],
        );

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name:
                "Complete product creation",
            },
          ),
        );

        expect(
          screen.getByText(
            /SKU-001.*Existing Product/i,
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            /SKU-NEW.*New Product/i,
          ),
        ).toBeInTheDocument();

        const numberInputs =
          screen.getAllByRole(
            "spinbutton",
          );

        expect(
          numberInputs[1],
        ).toHaveValue(125);

        expect(
          numberInputs[5],
        ).toHaveValue(250);
      },
    );

    it(
      "submits selected customer warehouse and product IDs",
      async () => {
        mockUseCustomerList
          .mockReturnValue({
            data: {
              customers: [
                customer,
              ],
            },
            isFetching: false,
            isPending: false,
          });

        const {
          onClose,
        } = await renderDialog();

        const customerInput =
          screen.getByPlaceholderText(
            "Search customer name, phone, email or code",
          );

        changeControl(
          customerInput,
          {
            target: {
              value: "Test",
            },
          },
        );

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name:
                /CUS-001.*Test Customer/i,
            },
          ),
        );

        changeControl(
          screen.getByRole(
            "combobox",
          ),
          {
            target: {
              value:
                "warehouse-1",
            },
          },
        );

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name:
                "Select existing product",
            },
          ),
        );

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name:
                "Create sales order",
            },
          ),
        );

        await waitFor(() => {
          expect(
            mockCreateMutateAsync,
          ).toHaveBeenCalledTimes(
            1,
          );
        });

        expect(
          mockCreateMutateAsync,
        ).toHaveBeenCalledWith(
          expect.objectContaining({
            customer_id:
              "customer-1",
            warehouse_id:
              "warehouse-1",
            items: [
              expect.objectContaining({
                product_id:
                  "product-existing",
                unit_price:
                  "125.00",
              }),
            ],
          }),
        );

        expect(
          onClose,
        ).toHaveBeenCalledTimes(
          1,
        );
      },
    );
  },
);
function changeControl(element:HTMLElement, event:{target:{value:string}}){
 if(element.getAttribute('role')==='combobox' && element.tagName==='INPUT'){
  const select=element.parentElement?.querySelector('select');
  const option=Array.from(select?.options??[]).find(o=>o.value===event.target.value);
  fireEvent.focus(element);fireEvent.change(element,{target:{value:option?.text??event.target.value}});
  const button=Array.from(document.querySelectorAll('[role="option"]')??[]).find(b=>b.textContent===option?.text);
  if(!button)throw new Error('Matching option not rendered');fireEvent.click(button);
 }else fireEvent.change(element,event);
}
