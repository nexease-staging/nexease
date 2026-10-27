"use client";

import {
  useEffect,
} from "react";

import {
  zodResolver,
} from "@hookform/resolvers/zod";

import {
  X,
} from "lucide-react";

import {
  useForm,
} from "react-hook-form";

import {
  z,
} from "zod";

import {
  useCategory,
  useCreateCategory,
  useUpdateCategory,
} from "@/features/categories/hooks";

import {
  APIRequestError,
} from "@/lib/api/client";


const categorySchema = z.object({
  name: z
    .string()
    .trim()
    .min(
      1,
      "Category name is required.",
    )
    .max(
      100,
      "Category name cannot exceed 100 characters.",
    ),

  description: z
    .string()
    .trim()
    .max(
      500,
      "Description cannot exceed 500 characters.",
    ),
});


type CategoryFormValues =
  z.infer<typeof categorySchema>;


const emptyValues: CategoryFormValues = {
  name: "",
  description: "",
};


interface CategoryDialogProps {
  open: boolean;
  categoryId: string | null;
  onClose: () => void;
}


function firstFieldMessage(
  value: unknown,
): string | null {
  if (
    Array.isArray(value)
    &&
    typeof value[0] === "string"
  ) {
    return value[0];
  }

  if (typeof value === "string") {
    return value;
  }

  return null;
}


export default function CategoryDialog({
  open,
  categoryId,
  onClose,
}: CategoryDialogProps) {
  const isEditing =
    Boolean(categoryId);

  const categoryQuery =
    useCategory(
      categoryId ?? "",
    );

  const createMutation =
    useCreateCategory();

  const updateMutation =
    useUpdateCategory();

  const resetCreateMutation =
    createMutation.reset;

  const resetUpdateMutation =
    updateMutation.reset;

  const {
    register,
    handleSubmit,
    reset,
    setError,
    formState: {
      errors,
    },
  } = useForm<CategoryFormValues>({
    resolver:
      zodResolver(
        categorySchema,
      ),
    defaultValues:
      emptyValues,
  });


  useEffect(() => {
    if (!open) {
      return;
    }

    resetCreateMutation();
    resetUpdateMutation();

    if (!categoryId) {
      reset(
        emptyValues,
      );
    }
  }, [
    categoryId,
    open,
    reset,
    resetCreateMutation,
    resetUpdateMutation,
  ]);


  useEffect(() => {
    if (
      !open
      ||
      !categoryId
      ||
      !categoryQuery.data
    ) {
      return;
    }

    const category =
      categoryQuery.data;

    reset({
      name:
        category.name,
      description:
        category.description
        ??
        "",
    });
  }, [
    categoryId,
    categoryQuery.data,
    open,
    reset,
  ]);


  function applyServerErrors(
    error: APIRequestError,
  ): void {
    if (!error.details) {
      return;
    }

    const nestedFields =
      error.details.fields;

    const fieldDetails =
      (
        nestedFields
        &&
        typeof nestedFields === "object"
      )
        ? nestedFields as Record<
            string,
            unknown
          >
        : error.details;

    const formFields: Array<
      keyof CategoryFormValues
    > = [
      "name",
      "description",
    ];

    for (const field of formFields) {
      const message =
        firstFieldMessage(
          fieldDetails[field],
        );

      if (message) {
        setError(
          field,
          {
            type: "server",
            message,
          },
        );
      }
    }
  }


  async function submit(
    values: CategoryFormValues,
  ): Promise<void> {
    try {
      if (categoryId) {
        await updateMutation.mutateAsync({
          categoryId,
          payload: {
            name:
              values.name,
            description:
              values.description,
          },
        });
      } else {
        await createMutation.mutateAsync({
          name:
            values.name,
          description:
            values.description,
        });
      }

      onClose();
    } catch (error) {
      if (
        error instanceof APIRequestError
      ) {
        applyServerErrors(
          error,
        );
      }
    }
  }


  if (!open) {
    return null;
  }


  const isPending =
    createMutation.isPending
    ||
    updateMutation.isPending;

  const mutationError =
    createMutation.error
    ??
    updateMutation.error;

  const generalError =
    mutationError instanceof Error
      ? mutationError.message
      : null;


  return (
    <div
      role="presentation"
      className="
        fixed inset-0 z-50
        flex items-center justify-center
        bg-slate-950/50 p-4
      "
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="category-dialog-title"
        className="
          max-h-[90vh] w-full
          max-w-xl overflow-y-auto
          rounded-2xl bg-white
          text-slate-900 shadow-2xl
        "
      >
        <div
          className="
            flex items-start
            justify-between border-b
            border-slate-200 p-5
          "
        >
          <div>
            <h2
              id="category-dialog-title"
              className="
                text-xl font-bold
                text-slate-900
              "
            >
              {isEditing
                ? "Edit category"
                : "New category"}
            </h2>

            <p
              className="
                mt-1 text-sm
                text-slate-500
              "
            >
              {isEditing
                ? (
                    "Update the category name "
                    +
                    "and description."
                  )
                : (
                    "Create a category for "
                    +
                    "organizing products."
                  )}
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            disabled={isPending}
            aria-label="Close"
            className="
              rounded-lg p-2
              text-slate-500
              hover:bg-slate-100
              hover:text-slate-900
              disabled:opacity-50
            "
          >
            <X size={20} />
          </button>
        </div>

        {isEditing
        && categoryQuery.isPending ? (
          <div
            className="
              flex min-h-52
              items-center justify-center
              p-6 text-sm
              text-slate-500
            "
          >
            Loading category...
          </div>
        ) : isEditing
        && categoryQuery.isError ? (
          <div
            className="
              p-6 text-sm
              text-red-700
            "
          >
            {categoryQuery.error.message}
          </div>
        ) : (
          <form
            onSubmit={
              handleSubmit(
                submit,
              )
            }
            className="space-y-5 p-5"
          >
            <label className="block space-y-1.5">
              <span
                className="
                  text-sm font-semibold
                  text-slate-700
                "
              >
                Category name
              </span>

              <input
                type="text"
                autoFocus
                {...register(
                  "name",
                )}
                placeholder="Example: Electronics"
                className="
                  h-10 w-full rounded-lg
                  border border-slate-300
                  bg-white px-3 text-sm
                  text-slate-900 outline-none
                  focus:border-blue-500
                  focus:ring-2
                  focus:ring-blue-100
                "
              />

              {errors.name ? (
                <p
                  className="
                    text-sm text-red-600
                  "
                >
                  {errors.name.message}
                </p>
              ) : null}
            </label>

            <label className="block space-y-1.5">
              <span
                className="
                  text-sm font-semibold
                  text-slate-700
                "
              >
                Description
              </span>

              <textarea
                rows={4}
                {...register(
                  "description",
                )}
                placeholder={
                  "Optional description "
                  +
                  "for this category"
                }
                className="
                  w-full resize-y rounded-lg
                  border border-slate-300
                  bg-white px-3 py-2
                  text-sm text-slate-900
                  outline-none
                  focus:border-blue-500
                  focus:ring-2
                  focus:ring-blue-100
                "
              />

              {errors.description ? (
                <p
                  className="
                    text-sm text-red-600
                  "
                >
                  {errors.description.message}
                </p>
              ) : null}
            </label>

            {generalError ? (
              <div
                className="
                  rounded-lg border
                  border-red-200 bg-red-50
                  px-4 py-3 text-sm
                  text-red-700
                "
              >
                {generalError}
              </div>
            ) : null}

            <div
              className="
                flex justify-end gap-3
                border-t border-slate-200
                pt-5
              "
            >
              <button
                type="button"
                onClick={onClose}
                disabled={isPending}
                className="
                  rounded-lg border
                  border-slate-300 bg-white
                  px-4 py-2 text-sm
                  font-semibold text-slate-700
                  hover:bg-slate-50
                  disabled:opacity-50
                "
              >
                Cancel
              </button>

              <button
                type="submit"
                disabled={isPending}
                className="
                  rounded-lg bg-blue-600
                  px-4 py-2 text-sm
                  font-semibold text-white
                  hover:bg-blue-700
                  disabled:cursor-not-allowed
                  disabled:opacity-50
                "
              >
                {isPending
                  ? "Saving..."
                  : isEditing
                    ? "Save changes"
                    : "Create category"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}