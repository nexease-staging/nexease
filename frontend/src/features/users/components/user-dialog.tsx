"use client";
import SearchSelect from "@/components/search-select";


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
  useCreateUser,
  useRoleLookup,
  useUpdateUser,
  useUser,
} from "@/features/users/hooks";

import {
  APIRequestError,
} from "@/lib/api/client";

const userSchema = z.object({
  email: z
    .email(
      "Enter a valid email address.",
    )
    .max(
      254,
      "Email cannot exceed 254 characters.",
    ),

  first_name: z
    .string()
    .trim()
    .min(
      1,
      "First name is required.",
    )
    .max(
      100,
      "First name cannot exceed 100 characters.",
    ),

  last_name: z
    .string()
    .trim()
    .min(
      1,
      "Last name is required.",
    )
    .max(
      100,
      "Last name cannot exceed 100 characters.",
    ),

  role_id: z
    .string()
    .trim()
    .min(
      1,
      "Select a role.",
    ),

  password: z
    .string()
    .max(
      128,
      "Password cannot exceed 128 characters.",
    ),

  password_confirmation: z
    .string()
    .max(
      128,
      "Password confirmation cannot exceed 128 characters.",
    ),
});

type UserFormValues =
  z.infer<typeof userSchema>;

const emptyValues: UserFormValues = {
  email: "",
  first_name: "",
  last_name: "",
  role_id: "",
  password: "",
  password_confirmation: "",
};

interface UserDialogProps {
  open: boolean;
  userId: string | null;
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

export default function UserDialog({
  open,
  userId,
  onClose,
}: UserDialogProps) {
  const isEditing =
    Boolean(userId);

  const userQuery =
    useUser(
      userId ?? "",
      open && isEditing,
    );

  const roleQuery =
    useRoleLookup({
      page: 1,
      page_size: 100,
      is_active: true,
      sort: "name",
    });

  const createMutation =
    useCreateUser();

  const updateMutation =
    useUpdateUser();

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
  } = useForm<UserFormValues>({
    resolver:
      zodResolver(
        userSchema,
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

    if (!userId) {
      reset(
        emptyValues,
      );
    }
  }, [
    open,
    reset,
    resetCreateMutation,
    resetUpdateMutation,
    userId,
  ]);

  useEffect(() => {
    if (
      !open
      ||
      !userId
      ||
      !userQuery.data
    ) {
      return;
    }

    const user =
      userQuery.data;

    reset({
      email:
        user.email,
      first_name:
        user.first_name,
      last_name:
        user.last_name,
      role_id:
        user.role?.id
        ??
        "",
      password: "",
      password_confirmation: "",
    });
  }, [
    open,
    reset,
    userId,
    userQuery.data,
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
      keyof UserFormValues
    > = [
      "email",
      "first_name",
      "last_name",
      "role_id",
      "password",
      "password_confirmation",
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
    values: UserFormValues,
  ): Promise<void> {
    if (!userId) {
      if (
        values.password.length < 8
      ) {
        setError(
          "password",
          {
            type: "validate",
            message:
              "Password must contain at least 8 characters.",
          },
        );

        return;
      }

      if (
        values.password
        !==
        values.password_confirmation
      ) {
        setError(
          "password_confirmation",
          {
            type: "validate",
            message:
              "Passwords do not match.",
          },
        );

        return;
      }
    }

    try {
      if (userId) {
        await updateMutation.mutateAsync({
          userId,
          input: {
            email:
              values.email,
            first_name:
              values.first_name,
            last_name:
              values.last_name,
            role_id:
              values.role_id,
          },
        });
      } else {
        await createMutation.mutateAsync({
          email:
            values.email,
          first_name:
            values.first_name,
          last_name:
            values.last_name,
          role_id:
            values.role_id,
          password:
            values.password,
          password_confirmation:
            values.password_confirmation,
        });
      }

      onClose();
    } catch (error) {
      if (
        error instanceof APIRequestError
      ) {
        applyServerErrors(error);
      }
    }
  }

  if (!open) {
    return null;
  }

  const roles =
    roleQuery.data
      ?.roles
      .filter(
        (role) =>
          role.is_active,
      )
    ??
    [];

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
        aria-labelledby="user-dialog-title"
        className="
          max-h-[90vh] w-full
          max-w-2xl overflow-y-auto
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
              id="user-dialog-title"
              className="
                text-xl font-bold
                text-slate-900
              "
            >
              {
                isEditing
                  ? "Edit user"
                  : "Create user"
              }
            </h2>

            <p
              className="
                mt-1 text-sm text-slate-600
              "
            >
              {
                isEditing
                  ? "Update user identity and role."
                  : "Add a user to this organization."
              }
            </p>
          </div>

          <button
            type="button"
            aria-label="Close"
            disabled={isPending}
            onClick={onClose}
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
        && userQuery.isPending ? (
          <div
            className="
              flex min-h-72 items-center
              justify-center text-sm
              text-slate-500
            "
          >
            Loading user…
          </div>
        ) : isEditing
        && userQuery.isError ? (
          <div
            className="
              flex min-h-72 flex-col
              items-center justify-center
              gap-3 p-6 text-center
            "
          >
            <p className="text-sm text-red-700">
              {userQuery.error.message}
            </p>

            <button
              type="button"
              onClick={() => {
                void userQuery.refetch();
              }}
              className="
                rounded-lg bg-slate-900
                px-4 py-2 text-sm
                font-semibold text-white
              "
            >
              Try again
            </button>
          </div>
        ) : (
          <form
            onSubmit={(event) => {
              void handleSubmit(
                submit,
              )(event);
            }}
            className="space-y-5 p-5"
          >
            <div
              className="
                grid gap-4 md:grid-cols-2
              "
            >
              <label className="space-y-1.5">
                <span className="text-sm font-semibold">
                  First name
                </span>

                <input
                  {...register("first_name")}
                  type="text"
                  placeholder="First name"
                  disabled={isPending}
                  className="
                    h-10 w-full rounded-lg
                    border border-slate-300
                    bg-white px-3 text-sm
                    text-slate-900
                    placeholder:text-slate-400
                    outline-none
                    focus:border-blue-500
                    focus:ring-2
                    focus:ring-blue-100
                    disabled:opacity-50
                  "
                />

                {errors.first_name ? (
                  <p className="text-sm text-red-600">
                    {errors.first_name.message}
                  </p>
                ) : null}
              </label>

              <label className="space-y-1.5">
                <span className="text-sm font-semibold">
                  Last name
                </span>

                <input
                  {...register("last_name")}
                  type="text"
                  placeholder="Last name"
                  disabled={isPending}
                  className="
                    h-10 w-full rounded-lg
                    border border-slate-300
                    bg-white px-3 text-sm
                    text-slate-900
                    placeholder:text-slate-400
                    outline-none
                    focus:border-blue-500
                    focus:ring-2
                    focus:ring-blue-100
                    disabled:opacity-50
                  "
                />

                {errors.last_name ? (
                  <p className="text-sm text-red-600">
                    {errors.last_name.message}
                  </p>
                ) : null}
              </label>
            </div>

            <label className="block space-y-1.5">
              <span className="text-sm font-semibold">
                Email
              </span>

              <input
                {...register("email")}
                type="email"
                placeholder="user@example.com"
                autoComplete="email"
                disabled={isPending}
                className="
                  h-10 w-full rounded-lg
                  border border-slate-300
                  bg-white px-3 text-sm
                  text-slate-900
                  placeholder:text-slate-400
                  outline-none
                  focus:border-blue-500
                  focus:ring-2
                  focus:ring-blue-100
                  disabled:opacity-50
                "
              />

              {errors.email ? (
                <p className="text-sm text-red-600">
                  {errors.email.message}
                </p>
              ) : null}
            </label>

            <label className="block space-y-1.5">
              <span className="text-sm font-semibold">
                Role
              </span>

              <SearchSelect
                {...register("role_id")}
                disabled={
                  isPending
                  ||
                  roleQuery.isPending
                }
                className="
                  h-10 w-full rounded-lg
                  border border-slate-300
                  bg-white px-3 text-sm
                  text-slate-900 outline-none
                  focus:border-blue-500
                  focus:ring-2
                  focus:ring-blue-100
                  disabled:opacity-50
                "
              >
                <option value="">
                  Select role
                </option>

                {roles.map(
                  (role) => (
                    <option
                      key={role.id}
                      value={role.id}
                    >
                      {role.name}
                    </option>
                  ),
                )}
              </SearchSelect>

              {errors.role_id ? (
                <p className="text-sm text-red-600">
                  {errors.role_id.message}
                </p>
              ) : null}
            </label>

            {!isEditing ? (
              <div
                className="
                  grid gap-4 md:grid-cols-2
                "
              >
                <label className="space-y-1.5">
                  <span className="text-sm font-semibold">
                    Password
                  </span>

                  <input
                    {...register("password")}
                    type="password"
                    placeholder="At least 8 characters"
                    autoComplete="new-password"
                    disabled={isPending}
                    className="
                      h-10 w-full rounded-lg
                      border border-slate-300
                      bg-white px-3 text-sm
                      text-slate-900
                      placeholder:text-slate-400
                      outline-none
                      focus:border-blue-500
                      focus:ring-2
                      focus:ring-blue-100
                      disabled:opacity-50
                    "
                  />

                  {errors.password ? (
                    <p className="text-sm text-red-600">
                      {errors.password.message}
                    </p>
                  ) : null}
                </label>

                <label className="space-y-1.5">
                  <span className="text-sm font-semibold">
                    Confirm password
                  </span>

                  <input
                    {...register(
                      "password_confirmation",
                    )}
                    type="password"
                    placeholder="Repeat password"
                    autoComplete="new-password"
                    disabled={isPending}
                    className="
                      h-10 w-full rounded-lg
                      border border-slate-300
                      bg-white px-3 text-sm
                      text-slate-900
                      placeholder:text-slate-400
                      outline-none
                      focus:border-blue-500
                      focus:ring-2
                      focus:ring-blue-100
                      disabled:opacity-50
                    "
                  />

                  {
                    errors
                      .password_confirmation
                    ? (
                      <p className="text-sm text-red-600">
                        {
                          errors
                            .password_confirmation
                            .message
                        }
                      </p>
                    )
                    : null
                  }
                </label>
              </div>
            ) : null}

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
                flex flex-col-reverse gap-3
                border-t border-slate-200
                pt-5 sm:flex-row
                sm:justify-end
              "
            >
              <button
                type="button"
                disabled={isPending}
                onClick={onClose}
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
                {
                  isPending
                    ? "Saving…"
                    : isEditing
                      ? "Save changes"
                      : "Create user"
                }
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}