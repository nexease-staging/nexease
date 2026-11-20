"""Read-only production reports over the selected orders."""

from decimal import Decimal
from .payroll import money


def production_rows(orders, report, product):
    if report == "materials":
        yield [
            "Order",
            "Warehouse",
            "Finished product",
            "Material",
            "Unit",
            "Required",
            "Net issued",
            "Estimated rate",
            "Actual material cost",
        ]
        for order in orders:
            for line in order["outputs"]:
                if product and line["product"] != product:
                    continue
                for m in line["materials"]:
                    yield [
                        order["number"],
                        order["warehouse_name"],
                        line["name"],
                        m["name"],
                        m["unit"],
                        m["required"],
                        m["issued"],
                        m["rate"],
                        m["value"],
                    ]
    elif report == "batches":
        yield [
            "Order",
            "Warehouse",
            "Finished product",
            "Unit",
            "Batch",
            "Status",
            "Accepted",
            "Rejected",
            "Yield %",
            "Batch cost",
        ]
        for order in orders:
            for line in order["outputs"]:
                if product and line["product"] != product:
                    continue
                for b in line.get("batches", []):
                    accepted = Decimal(b.get("accepted", 0))
                    rejected = Decimal(b.get("rejected", 0))
                    yield [
                        order["number"],
                        order["warehouse_name"],
                        line["name"],
                        line["unit"],
                        b["name"],
                        "Posted" if b["posted"] else "Open",
                        accepted,
                        rejected,
                        (
                            money(100 * accepted / (accepted + rejected))
                            if accepted + rejected
                            else ""
                        ),
                        b.get("cost", ""),
                    ]
    else:
        yield [
            "Order",
            "Sales order",
            "Due",
            "Status",
            "Finished item",
            "Unit",
            "Planned",
            "Accepted",
            "Rejected",
            "Pending",
            "Estimated cost",
            "Actual cost",
            "Variance",
            "Cost per accepted unit",
        ]
        for order in orders:
            for line in order["outputs"]:
                if product and line["product"] != product:
                    continue
                yield [
                    order["number"],
                    order["sales_number"],
                    order["due"],
                    order["status"],
                ] + [
                    line[k]
                    for k in (
                        "name",
                        "unit",
                        "quantity",
                        "accepted",
                        "rejected",
                        "pending",
                        "estimate",
                        "actual",
                        "variance",
                        "unit_cost",
                    )
                ]
