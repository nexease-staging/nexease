"use client";

import Link from "next/link";
import { useState } from "react";
import {
  useForm,
} from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import {
  forgotPassword,
} from "@/features/auth";
import {
  APIRequestError,
} from "@/lib/api/client";

const forgotPasswordSchema = z.object({
  email: z
    .string()
    .trim()
    .min(1, "Email is required.")
    .email("Enter a valid email address."),
});

type ForgotPasswordFormValues = z.infer<
  typeof forgotPasswordSchema
>;

export function ForgotPasswordForm() {
  const [successMessage, setSuccessMessage] =
    useState<string | null>(null);

  const [requestError, setRequestError] =
    useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: {
      errors,
      isSubmitting,
    },
  } = useForm<ForgotPasswordFormValues>({
    resolver: zodResolver(
      forgotPasswordSchema,
    ),
    defaultValues: {
      email: "",
    },
  });

  async function onSubmit(
    values: ForgotPasswordFormValues,
  ) {
    setRequestError(null);
    setSuccessMessage(null);

    try {
      const result = await forgotPassword({
        email: values.email,
      });

      setSuccessMessage(result.message);
    } catch (error) {
      if (error instanceof APIRequestError) {
        setRequestError(
          error.message ||
            "Unable to process the request.",
        );
        return;
      }

      setRequestError(
        "Unable to process the request. Please try again.",
      );
    }
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-2xl font-semibold">
          Forgot password
        </h1>

        <p className="text-sm text-muted-foreground">
          Enter your administrator email address
          and we&apos;ll send you a password reset
          link.
        </p>
      </div>

      {successMessage ? (
        <div
          className="rounded-md border p-4 text-sm"
          role="status"
        >
          {successMessage}
        </div>
      ) : null}

      {requestError ? (
        <div
          className="rounded-md border p-4 text-sm"
          role="alert"
        >
          {requestError}
        </div>
      ) : null}

      <form
        onSubmit={handleSubmit(onSubmit)}
        className="space-y-4"
      >
        <div className="space-y-2">
          <label
            htmlFor="email"
            className="text-sm font-medium"
          >
            Email
          </label>

          <input
            id="email"
            type="email"
            autoComplete="email"
            {...register("email")}
            className="w-full rounded-md border px-3 py-2 text-sm"
            placeholder="admin@example.com"
          />

          {errors.email ? (
            <p className="text-sm text-destructive">
              {errors.email.message}
            </p>
          ) : null}
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"
        >
          {isSubmitting
            ? "Sending..."
            : "Send reset link"}
        </button>
      </form>

      <div className="text-center text-sm">
        <Link
          href="/login"
          className="font-medium underline underline-offset-4"
        >
          Back to sign in
        </Link>
      </div>
    </div>
  );
}