import {
  render,
  screen,
} from "@testing-library/react";

import {
  describe,
  expect,
  it,
} from "vitest";

function TestComponent() {
  return (
    <div>
      Banking test environment
    </div>
  );
}

describe(
  "frontend test environment",
  () => {
    it(
      "renders a React component",
      () => {
        render(<TestComponent />);

        expect(
          screen.getByText(
            "Banking test environment",
          ),
        ).toBeInTheDocument();
      },
    );
  },
);