"use client";

import Link from "next/link";
import {
  useSearchParams,
} from "next/navigation";
import { useState } from "react";
import {
  useForm,
} from "react-hook-form";
import {
  zodResolver,
} from "@hookform/resolvers/zod";
import { z } from "zod";

import {
  resetPassword,
} from "@/features/auth";
import {
  APIRequestError,
} from "@/lib/api/client";

const resetPasswordSchema = z
  .object({
    password: z
      .string()
      .min(
        8,
        "Password must be at least 8 characters.",
      ),
    confirm_password: z
      .string()
      .min(
        1,
        "Confirm your new password.",
      ),
  })
  .refine(
    (values) =>
      values.password ===
      values.confirm_password,
    {
      message: "Passwords do not match.",
      path: ["confirm_password"],
    },
  );

type ResetPasswordFormValues = z.infer<
  typeof resetPasswordSchema
>;

export function ResetPasswordForm() {
  const searchParams = useSearchParams();

  const token = (
    searchParams.get("token") || ""
  ).trim();

  const [
    successMessage,
    setSuccessMessage,
  ] = useState<string | null>(null);

  const [
    requestError,
    setRequestError,
  ] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: {
      errors,
      isSubmitting,
    },
  } = useForm<ResetPasswordFormValues>({
    resolver: zodResolver(
      resetPasswordSchema,
    ),
    defaultValues: {
      password: "",
      confirm_password: "",
    },
  });

  async function onSubmit(
    values: ResetPasswordFormValues,
  ) {
    if (!token) {
      setRequestError(
        "This password reset link is invalid or has expired.",
      );
      return;
    }

    setRequestError(null);
    setSuccessMessage(null);

    try {
      const result = await resetPassword({
        token,
        new_password: values.password,
      });

      setSuccessMessage(
        result.message,
      );
    } catch (error) {
      if (
        error instanceof APIRequestError
      ) {
        setRequestError(
          error.message ||
            "Unable to reset your password.",
        );
        return;
      }

      setRequestError(
        "Unable to reset your password. Please try again.",
      );
    }
  }

  if (!token) {
    return (
      <div className="space-y-6">
        <div className="space-y-2">
          <h1 className="text-2xl font-semibold">
            Reset password
          </h1>

          <p
            className="text-sm text-destructive"
            role="alert"
          >
            This password reset link is invalid
            or has expired.
          </p>
        </div>

        <Link
          href="/forgot-password"
          className="text-sm font-medium underline underline-offset-4"
        >
          Request a new reset link
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-2xl font-semibold">
          Reset password
        </h1>

        <p className="text-sm text-muted-foreground">
          Enter a new password for your
          NexEase account.
        </p>
      </div>

      {successMessage ? (
        <div
          className="space-y-4"
          role="status"
        >
          <div className="rounded-md border p-4 text-sm">
            {successMessage}
          </div>

          <Link
            href="/login"
            className="inline-block text-sm font-medium underline underline-offset-4"
          >
            Sign in with new password
          </Link>
        </div>
      ) : (
        <>
          {requestError ? (
            <div
              className="rounded-md border p-4 text-sm text-destructive"
              role="alert"
            >
              {requestError}
            </div>
          ) : null}

          <form
            onSubmit={handleSubmit(
              onSubmit,
            )}
            className="space-y-4"
          >
            <div className="space-y-2">
              <label
                htmlFor="password"
                className="text-sm font-medium"
              >
                New password
              </label>

              <input
                id="password"
                type="password"
                autoComplete="new-password"
                {...register("password")}
                className="w-full rounded-md border px-3 py-2 text-sm"
              />

              {errors.password ? (
                <p className="text-sm text-destructive">
                  {errors.password.message}
                </p>
              ) : null}
            </div>

            <div className="space-y-2">
              <label
                htmlFor="confirm_password"
                className="text-sm font-medium"
              >
                Confirm new password
              </label>

              <input
                id="confirm_password"
                type="password"
                autoComplete="new-password"
                {...register(
                  "confirm_password",
                )}
                className="w-full rounded-md border px-3 py-2 text-sm"
              />

              {errors.confirm_password ? (
                <p className="text-sm text-destructive">
                  {
                    errors
                      .confirm_password
                      .message
                  }
                </p>
              ) : null}
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"
            >
              {isSubmitting
                ? "Resetting..."
                : "Reset password"}
            </button>
          </form>
        </>
      )}

      {!successMessage ? (
        <div className="text-center text-sm">
          <Link
            href="/login"
            className="font-medium underline underline-offset-4"
          >
            Back to sign in
          </Link>
        </div>
      ) : null}
    </div>
  );
}