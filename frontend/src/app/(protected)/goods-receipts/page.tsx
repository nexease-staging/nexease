"use client";
import SearchSelect from "@/components/search-select";


import {
  useDeferredValue,
  useState,
} from "react";

import {
  ChevronLeft,
  ChevronRight,
  Eye,
  PackageCheck,
  Plus,
  Search,
} from "lucide-react";

import {
  useAuth,
} from "@/features/auth/auth-context";

import GoodsReceiptDetailDialog from "@/features/goods-receipts/components/goods-receipt-detail-dialog";
import GoodsReceiptDialog from "@/features/goods-receipts/components/goods-receipt-dialog";

import {
  useGoodsReceiptList,
} from "@/features/goods-receipts/hooks";

import type {
  GoodsReceiptSummary,
} from "@/features/goods-receipts/types";

import {
  APIRequestError,
} from "@/lib/api/client";

const PAGE_SIZE = 25;

function formatDateTime(
  value: string | null,
): string {
  if (!value) {
    return "—";
  }

  const parsedDate =
    new Date(value);

  if (
    Number.isNaN(
      parsedDate.getTime(),
    )
  ) {
    return value;
  }

  return new Intl.DateTimeFormat(
    "en-IN",
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    },
  ).format(
    parsedDate,
  );
}

function getErrorMessage(
  error: unknown,
): string {
  if (
    error
    instanceof
    APIRequestError
  ) {
    return error.message;
  }

  if (
    error
    instanceof
    Error
  ) {
    return error.message;
  }

  return (
    "Unable to load goods receipts."
  );
}

export default function GoodsReceiptsPage() {
  const {
    authentication,
  } = useAuth();

  const [
    page,
    setPage,
  ] = useState(1);

  const [
    search,
    setSearch,
  ] = useState("");

  const [
    sort,
    setSort,
  ] = useState(
    "-created_at",
  );

  const [
    createOpen,
    setCreateOpen,
  ] = useState(false);

  const [
    detailOpen,
    setDetailOpen,
  ] = useState(false);

  const [
    selectedGoodsReceiptId,
    setSelectedGoodsReceiptId,
  ] = useState("");

  const deferredSearch =
    useDeferredValue(
      search.trim(),
    );

  const permissions =
    authentication
      ?.role
      .permissions
      ??
      [];

  const canCreate =
    permissions.includes(
      "goods_receipts.create",
    );

  const goodsReceiptQuery =
    useGoodsReceiptList({
      page,
      page_size: PAGE_SIZE,
      search:
        deferredSearch
        ||
        undefined,
      sort,
    });

  const goodsReceipts =
    goodsReceiptQuery
      .data
      ?.goods_receipts
      ??
      [];

  const pagination =
    goodsReceiptQuery
      .data
      ?.pagination;

  function openDetail(
    goodsReceiptId: string,
  ): void {
    setSelectedGoodsReceiptId(
      goodsReceiptId,
    );

    setCreateOpen(false);
    setDetailOpen(true);
  }

  function handleCreated(
    goodsReceiptId: string,
  ): void {
    setCreateOpen(false);

    setSelectedGoodsReceiptId(
      goodsReceiptId,
    );

    setDetailOpen(true);
  }

  return (
    <>
      <div className="space-y-6">
        <header
          className="
            flex flex-col gap-4
            sm:flex-row
            sm:items-start
            sm:justify-between
          "
        >
          <div>
            <p
              className="
                text-sm font-semibold
                text-blue-600
              "
            >
              Purchasing
            </p>

            <h1
              className="
                mt-1 text-2xl
                font-bold tracking-tight
                text-slate-950
                sm:text-3xl
              "
            >
              Goods Receipts
            </h1>

            <p
              className="
                mt-2 max-w-2xl
                text-sm text-slate-600
              "
            >
              Receive purchase-order items,
              update inventory and review
              receiving history.
            </p>
          </div>

          {canCreate
            ? (
              <button
                type="button"
                onClick={() => {
                  setDetailOpen(false);
                  setCreateOpen(true);
                }}
                className="
                  inline-flex items-center
                  justify-center gap-2
                  rounded-lg bg-blue-600
                  px-4 py-2.5 text-sm
                  font-semibold text-white
                  shadow-sm
                  hover:bg-blue-700
                "
              >
                <Plus size={18} />
                Receive goods
              </button>
            )
            : null}
        </header>

        <section
          className="
            rounded-xl border
            border-slate-200 bg-white
            p-4 shadow-sm
          "
        >
          <div
            className="
              grid gap-3
              md:grid-cols-[minmax(0,1fr)_220px]
            "
          >
            <label className="relative block">
              <span className="sr-only">
                Search goods receipts
              </span>

              <Search
                size={18}
                className="
                  pointer-events-none
                  absolute left-3 top-1/2
                  -translate-y-1/2
                  text-slate-400
                "
              />

              <input
                type="search"
                value={search}
                placeholder="
                  Search by GRN number
                "
                onChange={(event) => {
                  setSearch(
                    event.currentTarget
                      .value,
                  );

                  setPage(1);
                }}
                className="
                  h-11 w-full rounded-lg
                  border border-slate-300
                  bg-white py-2 pl-10
                  pr-3 text-sm
                  text-slate-950
                  outline-none
                  placeholder:text-slate-400
                  focus:border-blue-500
                  focus:ring-2
                  focus:ring-blue-100
                "
              />
            </label>

            <SearchSelect
              aria-label="
                Sort goods receipts
              "
              value={sort}
              onChange={(event) => {
                setSort(
                  event.currentTarget
                    .value,
                );

                setPage(1);
              }}
              className="
                h-11 w-full rounded-lg
                border border-slate-300
                bg-white px-3 text-sm
                text-slate-950
                outline-none
                focus:border-blue-500
                focus:ring-2
                focus:ring-blue-100
              "
            >
              <option value="-created_at">
                Newest first
              </option>

              <option value="created_at">
                Oldest first
              </option>

              <option value="-received_at">
                Latest received
              </option>

              <option value="received_at">
                Earliest received
              </option>

              <option value="grn_number">
                GRN number
              </option>
            </SearchSelect>
          </div>
        </section>

        {goodsReceiptQuery.isLoading
          ? (
            <section
              className="
                rounded-xl border
                border-slate-200 bg-white
                px-5 py-14 text-center
                text-sm text-slate-600
                shadow-sm
              "
            >
              Loading goods receipts…
            </section>
          )
          : null}

        {goodsReceiptQuery.isError
          ? (
            <section
              className="
                rounded-xl border
                border-red-200 bg-red-50
                px-5 py-4 text-sm
                text-red-700
              "
            >
              <p>
                {getErrorMessage(
                  goodsReceiptQuery.error,
                )}
              </p>

              <button
                type="button"
                onClick={() => {
                  void goodsReceiptQuery
                    .refetch();
                }}
                className="
                  mt-3 font-semibold
                  underline
                "
              >
                Try again
              </button>
            </section>
          )
          : null}

        {!goodsReceiptQuery.isLoading
        &&
        !goodsReceiptQuery.isError
        &&
        goodsReceipts.length === 0
          ? (
            <section
              className="
                rounded-xl border
                border-dashed
                border-slate-300 bg-white
                px-5 py-14 text-center
                shadow-sm
              "
            >
              <PackageCheck
                size={40}
                className="
                  mx-auto text-slate-400
                "
              />

              <h2
                className="
                  mt-4 font-bold
                  text-slate-950
                "
              >
                No goods receipts found
              </h2>

              <p
                className="
                  mx-auto mt-2
                  max-w-md text-sm
                  text-slate-600
                "
              >
                {search
                  ? (
                    "No receipt matches "
                    +
                    "your search."
                  )
                  : (
                    "Receive stock against "
                    +
                    "a confirmed purchase "
                    +
                    "order to create a GRN."
                  )}
              </p>

              {canCreate
              &&
              !search
                ? (
                  <button
                    type="button"
                    onClick={() => {
                      setCreateOpen(true);
                    }}
                    className="
                      mt-5 inline-flex
                      items-center gap-2
                      rounded-lg bg-blue-600
                      px-4 py-2.5 text-sm
                      font-semibold text-white
                      hover:bg-blue-700
                    "
                  >
                    <Plus size={18} />
                    Receive goods
                  </button>
                )
                : null}
            </section>
          )
          : null}

        {goodsReceipts.length > 0
          ? (
            <>
              <section
                className="
                  space-y-3 lg:hidden
                "
              >
                {goodsReceipts.map(
                  (goodsReceipt) => (
                    <GoodsReceiptCard
                      key={
                        goodsReceipt.id
                      }
                      goodsReceipt={
                        goodsReceipt
                      }
                      onOpen={() => {
                        openDetail(
                          goodsReceipt.id,
                        );
                      }}
                    />
                  ),
                )}
              </section>

              <section
                className="
                  hidden overflow-hidden
                  rounded-xl border
                  border-slate-200
                  bg-white shadow-sm
                  lg:block
                "
              >
                <div
                  className="
                    overflow-x-auto
                  "
                >
                  <table
                    className="
                      min-w-full divide-y
                      divide-slate-200
                    "
                  >
                    <thead
                      className="
                        bg-slate-50
                      "
                    >
                      <tr>
                        {[
                          "GRN number",
                          "Purchase order",
                          "Supplier",
                          "Warehouse",
                          "Items",
                          "Received at",
                          "Actions",
                        ].map(
                          (heading) => (
                            <th
                              key={heading}
                              className="
                                whitespace-nowrap
                                px-4 py-3
                                text-left text-xs
                                font-semibold
                                uppercase
                                tracking-wide
                                text-slate-600
                              "
                            >
                              {heading}
                            </th>
                          ),
                        )}
                      </tr>
                    </thead>

                    <tbody
                      className="
                        divide-y
                        divide-slate-200
                        bg-white
                      "
                    >
                      {goodsReceipts.map(
                        (goodsReceipt) => (
                          <tr
                            key={
                              goodsReceipt.id
                            }
                            className="
                              hover:bg-slate-50
                            "
                          >
                            <td
                              className="
                                whitespace-nowrap
                                px-4 py-4
                              "
                            >
                              <button
                                type="button"
                                onClick={() => {
                                  openDetail(
                                    goodsReceipt
                                      .id,
                                  );
                                }}
                                className="
                                  font-semibold
                                  text-blue-700
                                  hover:underline
                                "
                              >
                                {
                                  goodsReceipt
                                    .grn_number
                                }
                              </button>
                            </td>

                            <td
                              className="
                                whitespace-nowrap
                                px-4 py-4
                                text-sm
                                text-slate-700
                              "
                            >
                              {
                                goodsReceipt
                                  .purchase_order
                                  .po_number
                              }
                            </td>

                            <td
                              className="
                                min-w-48
                                px-4 py-4
                              "
                            >
                              <p
                                className="
                                  font-medium
                                  text-slate-950
                                "
                              >
                                {
                                  goodsReceipt
                                    .supplier.name
                                }
                              </p>

                              <p
                                className="
                                  mt-1 text-xs
                                  text-slate-500
                                "
                              >
                                {
                                  goodsReceipt
                                    .supplier.code
                                }
                              </p>
                            </td>

                            <td
                              className="
                                min-w-44
                                px-4 py-4
                              "
                            >
                              <p
                                className="
                                  text-sm font-medium
                                  text-slate-900
                                "
                              >
                                {
                                  goodsReceipt
                                    .warehouse.name
                                }
                              </p>

                              <p
                                className="
                                  mt-1 text-xs
                                  text-slate-500
                                "
                              >
                                {
                                  goodsReceipt
                                    .warehouse.code
                                }
                              </p>
                            </td>

                            <td
                              className="
                                px-4 py-4
                                text-sm
                                text-slate-700
                              "
                            >
                              {
                                goodsReceipt
                                  .item_count
                              }
                            </td>

                            <td
                              className="
                                whitespace-nowrap
                                px-4 py-4
                                text-sm
                                text-slate-700
                              "
                            >
                              {formatDateTime(
                                goodsReceipt
                                  .received_at,
                              )}
                            </td>

                            <td
                              className="
                                px-4 py-4
                              "
                            >
                              <button
                                type="button"
                                aria-label={
                                  (
                                    "View "
                                    +
                                    goodsReceipt
                                      .grn_number
                                  )
                                }
                                onClick={() => {
                                  openDetail(
                                    goodsReceipt
                                      .id,
                                  );
                                }}
                                className="
                                  rounded-lg p-2
                                  text-slate-500
                                  hover:bg-blue-50
                                  hover:text-blue-700
                                "
                              >
                                <Eye size={18} />
                              </button>
                            </td>
                          </tr>
                        ),
                      )}
                    </tbody>
                  </table>
                </div>
              </section>
            </>
          )
          : null}

        {pagination
        &&
        pagination.total_pages > 1
          ? (
            <nav
              aria-label="
                Goods receipt pagination
              "
              className="
                flex flex-col gap-3
                rounded-xl border
                border-slate-200 bg-white
                px-4 py-3 shadow-sm
                sm:flex-row sm:items-center
                sm:justify-between
              "
            >
              <p
                className="
                  text-sm text-slate-600
                "
              >
                Page{" "}
                <strong
                  className="
                    text-slate-950
                  "
                >
                  {pagination.page}
                </strong>{" "}
                of{" "}
                <strong
                  className="
                    text-slate-950
                  "
                >
                  {
                    pagination
                      .total_pages
                  }
                </strong>
                {" · "}
                {
                  pagination
                    .total_items
                }{" "}
                receipts
              </p>

              <div
                className="
                  flex items-center gap-2
                "
              >
                <button
                  type="button"
                  disabled={
                    !pagination
                      .has_previous
                  }
                  onClick={() => {
                    setPage(
                      (current) =>
                        Math.max(
                          1,
                          current - 1,
                        ),
                    );
                  }}
                  className="
                    inline-flex items-center
                    gap-1 rounded-lg
                    border border-slate-300
                    px-3 py-2 text-sm
                    font-semibold
                    text-slate-700
                    hover:bg-slate-50
                    disabled:opacity-50
                  "
                >
                  <ChevronLeft
                    size={17}
                  />
                  Previous
                </button>

                <button
                  type="button"
                  disabled={
                    !pagination.has_next
                  }
                  onClick={() => {
                    setPage(
                      (current) =>
                        current + 1,
                    );
                  }}
                  className="
                    inline-flex items-center
                    gap-1 rounded-lg
                    border border-slate-300
                    px-3 py-2 text-sm
                    font-semibold
                    text-slate-700
                    hover:bg-slate-50
                    disabled:opacity-50
                  "
                >
                  Next
                  <ChevronRight
                    size={17}
                  />
                </button>
              </div>
            </nav>
          )
          : null}
      </div>

      <GoodsReceiptDialog
        open={createOpen}
        onClose={() => {
          setCreateOpen(false);
        }}
        onCreated={handleCreated}
      />

      <GoodsReceiptDetailDialog
        open={detailOpen}
        goodsReceiptId={
          selectedGoodsReceiptId
        }
        onClose={() => {
          setDetailOpen(false);
        }}
      />
    </>
  );
}

interface GoodsReceiptCardProps {
  goodsReceipt:
    GoodsReceiptSummary;
  onOpen: () => void;
}

function GoodsReceiptCard({
  goodsReceipt,
  onOpen,
}: GoodsReceiptCardProps) {
  return (
    <article
      className="
        rounded-xl border
        border-slate-200 bg-white
        p-4 shadow-sm
      "
    >
      <div
        className="
          flex items-start
          justify-between gap-3
        "
      >
        <div className="min-w-0">
          <button
            type="button"
            onClick={onOpen}
            className="
              font-bold text-blue-700
              hover:underline
            "
          >
            {goodsReceipt.grn_number}
          </button>

          <p
            className="
              mt-1 truncate text-sm
              font-medium text-slate-950
            "
          >
            {
              goodsReceipt
                .supplier.name
            }
          </p>

          <p
            className="
              mt-1 text-xs
              text-slate-500
            "
          >
            {
              goodsReceipt
                .purchase_order
                .po_number
            }
          </p>
        </div>

        <span
          className="
            shrink-0 rounded-full
            bg-emerald-100
            px-2.5 py-1
            text-xs font-semibold
            text-emerald-700
          "
        >
          Received
        </span>
      </div>

      <dl
        className="
          mt-4 grid grid-cols-2
          gap-3 text-sm
        "
      >
        <div>
          <dt
            className="
              text-xs text-slate-500
            "
          >
            Warehouse
          </dt>

          <dd
            className="
              mt-1 font-medium
              text-slate-900
            "
          >
            {
              goodsReceipt
                .warehouse.code
            }
          </dd>
        </div>

        <div>
          <dt
            className="
              text-xs text-slate-500
            "
          >
            Items
          </dt>

          <dd
            className="
              mt-1 font-medium
              text-slate-900
            "
          >
            {goodsReceipt.item_count}
          </dd>
        </div>

        <div className="col-span-2">
          <dt
            className="
              text-xs text-slate-500
            "
          >
            Received at
          </dt>

          <dd
            className="
              mt-1 font-medium
              text-slate-900
            "
          >
            {formatDateTime(
              goodsReceipt.received_at,
            )}
          </dd>
        </div>
      </dl>

      <button
        type="button"
        onClick={onOpen}
        className="
          mt-4 inline-flex w-full
          items-center justify-center
          gap-2 rounded-lg border
          border-slate-300 px-4 py-2
          text-sm font-semibold
          text-slate-700
          hover:bg-slate-50
        "
      >
        <Eye size={17} />
        View details
      </button>
    </article>
  );
}