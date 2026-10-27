"use client";

import {
  useEffect,
  useRef,
  useState,
} from "react";

export interface SearchComboboxOption {
  id: string;
  label: string;
  description?: string;
}

interface SearchComboboxProps {
  value: string;
  searchValue: string;
  options: SearchComboboxOption[];
  placeholder?: string;
  minimumSearchLength?: number;
  disabled?: boolean;
  isLoading?: boolean;
  emptyMessage?: string;
  createLabel?: string;
  canCreate?: boolean;
  onSearchChange: (
    value: string,
  ) => void;
  onSelect: (
    option: SearchComboboxOption,
  ) => void;
  onCreate?: (
    searchValue: string,
  ) => void;
  onClear?: () => void;
}

export function SearchCombobox({
  value,
  searchValue,
  options,
  placeholder = "Search...",
  minimumSearchLength = 3,
  disabled = false,
  isLoading = false,
  emptyMessage = "No matches found.",
  createLabel,
  canCreate = false,
  onSearchChange,
  onSelect,
  onCreate,
  onClear,
}: SearchComboboxProps) {
  const containerRef =
    useRef<HTMLDivElement | null>(
      null,
    );

  const [
    isOpen,
    setIsOpen,
  ] = useState(false);

  const normalizedSearch =
    searchValue.trim();

  const canSearch =
    normalizedSearch.length
    >=
    minimumSearchLength;

  useEffect(() => {
    function handlePointerDown(
      event: MouseEvent,
    ) {
      if (
        containerRef.current
        &&
        !containerRef.current.contains(
          event.target as Node,
        )
      ) {
        setIsOpen(false);
      }
    }

    document.addEventListener(
      "mousedown",
      handlePointerDown,
    );

    return () => {
      document.removeEventListener(
        "mousedown",
        handlePointerDown,
      );
    };
  }, []);

  const showCreate =
    canSearch
    &&
    canCreate
    &&
    Boolean(onCreate);

  return (
    <div
      ref={containerRef}
      className="relative"
    >
      <div className="relative">
        <input
          type="text"
          value={searchValue}
          placeholder={placeholder}
          disabled={disabled}
          autoComplete="off"
          onFocus={() => {
            setIsOpen(true);
          }}
          onChange={(event) => {
            onSearchChange(
              event.target.value,
            );

            setIsOpen(true);
          }}
          className="
            w-full rounded-lg border
            border-slate-300 bg-white
            px-3 py-2 pr-9 text-sm
            text-slate-900 outline-none
            transition
            placeholder:text-slate-400
            focus:border-slate-500
            focus:ring-2
            focus:ring-slate-200
            disabled:cursor-not-allowed
            disabled:bg-slate-100
            disabled:text-slate-500
          "
        />

        {value ? (
          <button
            type="button"
            disabled={disabled}
            aria-label="Clear selection"
            onClick={() => {
              onClear?.();
              setIsOpen(false);
            }}
            className="
              absolute right-2 top-1/2
              -translate-y-1/2
              rounded px-1 text-lg
              leading-none text-slate-400
              hover:text-slate-700
              disabled:cursor-not-allowed
            "
          >
            ×
          </button>
        ) : null}
      </div>

      {isOpen ? (
        <div
          className="
            absolute z-50 mt-1
            max-h-64 w-full
            overflow-y-auto rounded-lg
            border border-slate-200
            bg-white py-1 shadow-lg
          "
        >
          {!canSearch ? (
            <p
              className="
                px-3 py-2 text-sm
                text-slate-500
              "
            >
              Type at least{" "}
              {minimumSearchLength}{" "}
              characters to search.
            </p>
          ) : isLoading ? (
            <p
              className="
                px-3 py-2 text-sm
                text-slate-500
              "
            >
              Searching...
            </p>
          ) : (
            <>
              {options.length > 0 ? (
                options.map(
                  (option) => (
                    <button
                      key={option.id}
                      type="button"
                      onClick={() => {
                        onSelect(option);
                        setIsOpen(false);
                      }}
                      className="
                        block w-full
                        px-3 py-2 text-left
                        hover:bg-slate-50
                        focus:bg-slate-50
                        focus:outline-none
                      "
                    >
                      <span
                        className="
                          block text-sm
                          font-semibold
                          text-slate-900
                        "
                      >
                        {option.label}
                      </span>

                      {option.description ? (
                        <span
                          className="
                            mt-0.5 block
                            text-xs
                            text-slate-500
                          "
                        >
                          {option.description}
                        </span>
                      ) : null}
                    </button>
                  ),
                )
              ) : (
                <p
                  className="
                    px-3 py-2 text-sm
                    text-slate-500
                  "
                >
                  {emptyMessage}
                </p>
              )}

              {showCreate ? (
                <button
                  type="button"
                  onClick={() => {
                    onCreate?.(
                      normalizedSearch,
                    );

                    setIsOpen(false);
                  }}
                  className="
                    block w-full
                    border-t
                    border-slate-100
                    px-3 py-2
                    text-left text-sm
                    font-semibold
                    text-slate-900
                    hover:bg-slate-50
                    focus:bg-slate-50
                    focus:outline-none
                  "
                >
                  {createLabel
                    ??
                    `Create "${normalizedSearch}"`}
                </button>
              ) : null}
            </>
          )}
        </div>
      ) : null}
    </div>
  );
}