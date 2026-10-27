"use client";

import {
  useEffect,
  useState,
} from "react";

import Link from "next/link";

import {
  useRouter,
  useSearchParams,
} from "next/navigation";

import {
  useForm,
} from "react-hook-form";

import {
  zodResolver,
} from "@hookform/resolvers/zod";

import {
  z,
} from "zod";

import {
  APIRequestError,
} from "@/lib/api/client";

import {
  useAuth,
} from "@/features/auth/auth-context";

const loginSchema = z.object({
  email: z
    .string()
    .trim()
    .min(
      1,
      "Email is required.",
    )
    .email(
      "Enter a valid email address.",
    ),

  password: z
    .string()
    .min(
      1,
      "Password is required.",
    ),
});

type LoginFormValues =
  z.infer<typeof loginSchema>;

export default function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const signupSucceeded =
    searchParams.get("signup")
    ===
    "success";

  const {
    signIn,
    status,
    isAuthenticated,
  } = useAuth();

  const [
    serverError,
    setServerError,
  ] = useState<string | null>(
    null,
  );

  const {
    register,
    handleSubmit,
    formState: {
      errors,
      isSubmitting,
    },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(
      loginSchema,
    ),

    defaultValues: {
      email: "",
      password: "",
    },
  });

  useEffect(() => {
    if (isAuthenticated) {
      router.replace(
        "/dashboard",
      );
    }
  }, [
    isAuthenticated,
    router,
  ]);

  async function onSubmit(
    values: LoginFormValues,
  ): Promise<void> {
    setServerError(null);

    try {
      await signIn(values);

      router.replace(
        "/dashboard",
      );

      router.refresh();
    } catch (error) {
      if (
        error instanceof APIRequestError
      ) {
        setServerError(
          error.message,
        );

        return;
      }

      setServerError(
        "Unable to sign in. Please try again.",
      );
    }
  }

  if (
    status === "loading"
    ||
    isAuthenticated
  ) {
    return (
      <div
        className="
          rounded-xl border border-slate-200
          bg-white p-8 text-center shadow-sm
        "
      >
        <p className="text-sm text-slate-600">
          Checking your session…
        </p>
      </div>
    );
  }

  return (
    <form
      onSubmit={handleSubmit(
        onSubmit,
      )}
      className="
        space-y-6 rounded-2xl
        border border-slate-200
        bg-white p-8 shadow-xl
        shadow-slate-200/60
      "
      noValidate
    >
      <div>
        <p
          className="
            text-sm font-semibold
            uppercase tracking-wider
            text-blue-600
          "
        >
          NexEase
        </p>

        <h1
          className="
            mt-2 text-3xl font-bold
            tracking-tight text-slate-900
          "
        >
          Sign in
        </h1>

        <p
          className="
            mt-2 text-sm text-slate-600
          "
        >
          Access your inventory management
          workspace.
        </p>
      </div>

      {signupSucceeded && (
        <div
          role="status"
          className="
            rounded-lg border border-emerald-200
            bg-emerald-50 px-4 py-3
            text-sm text-emerald-700
          "
        >
          Organization created successfully.
          Sign in with your administrator
          account.
        </div>
      )}

      {serverError && (
        <div
          role="alert"
          className="
            rounded-lg border border-red-200
            bg-red-50 px-4 py-3
            text-sm text-red-700
          "
        >
          {serverError}
        </div>
      )}

      <div>
        <label
          htmlFor="email"
          className="
            block text-sm font-medium
            text-slate-700
          "
        >
          Email
        </label>

        <input
          id="email"
          type="email"
          autoComplete="email"
          {...register("email")}
          className="
            mt-2 w-full rounded-lg
            border border-slate-300
            px-3 py-2.5 text-slate-900
            outline-none transition
            placeholder:text-slate-400
            focus:border-blue-500
            focus:ring-4
            focus:ring-blue-100
          "
          placeholder="admin@example.com"
        />

        {errors.email && (
          <p
            className="
              mt-1.5 text-sm text-red-600
            "
          >
            {errors.email.message}
          </p>
        )}
      </div>

      <div>
        <div
          className="
            flex items-center justify-between
          "
        >
          <label
            htmlFor="password"
            className="
              text-sm font-medium
              text-slate-700
            "
          >
            Password
          </label>

          <Link
            href="/forgot-password"
            className="
              text-sm font-semibold
              text-blue-600
              hover:text-blue-700
            "
          >
            Forgot password?
          </Link>
        </div>

        <input
          id="password"
          type="password"
          autoComplete="current-password"
          {...register("password")}
          className="
            mt-2 w-full rounded-lg
            border border-slate-300
            px-3 py-2.5 text-slate-900
            outline-none transition
            placeholder:text-slate-400
            focus:border-blue-500
            focus:ring-4
            focus:ring-blue-100
          "
          placeholder="Enter your password"
        />

        {errors.password && (
          <p
            className="
              mt-1.5 text-sm text-red-600
            "
          >
            {errors.password.message}
          </p>
        )}
      </div>

      <button
        type="submit"
        disabled={isSubmitting}
        className="
          w-full rounded-lg bg-blue-600
          px-4 py-2.5 font-semibold
          text-white transition
          hover:bg-blue-700
          focus:outline-none
          focus:ring-4
          focus:ring-blue-200
          disabled:cursor-not-allowed
          disabled:opacity-60
        "
      >
        {isSubmitting
          ? "Signing in…"
          : "Sign in"}
      </button>

      <div
        className="
          border-t border-slate-200 pt-5
          text-center
        "
      >
        <p
          className="
            text-sm text-slate-600
          "
        >
          New to NexEase?{" "}

          <Link
            href="/signup"
            className="
              font-semibold text-blue-600
              hover:text-blue-700
            "
          >
            Create an organization
          </Link>
        </p>
      </div>
    </form>
  );
}