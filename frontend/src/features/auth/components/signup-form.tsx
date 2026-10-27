"use client";
import SearchSelect from "@/components/search-select";


import {
  useState,
} from "react";

import Link from "next/link";
import {
  useRouter,
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
  signup,
} from "@/features/auth/api";

const signupSchema = z
  .object({
    business_scope: z.string().min(1),
    organization_name: z
      .string()
      .trim()
      .min(
        1,
        "Organization name is required.",
      ),

    organization_email: z
      .string()
      .trim()
      .min(
        1,
        "Organization email is required.",
      )
      .email(
        "Enter a valid organization email address.",
      ),

    phone: z
      .string()
      .trim()
      .optional(),

    first_name: z
      .string()
      .trim()
      .min(
        1,
        "First name is required.",
      ),

    last_name: z
      .string()
      .trim()
      .min(
        1,
        "Last name is required.",
      ),

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
        8,
        "Password must contain at least 8 characters.",
      ),

    confirm_password: z
      .string()
      .min(
        1,
        "Confirm your password.",
      ),
  })
  .refine(
    (values) =>
      values.password
      ===
      values.confirm_password,
    {
      message:
        "Passwords do not match.",
      path: [
        "confirm_password",
      ],
    },
  );

type SignupFormValues =
  z.infer<typeof signupSchema>;

const inputClassName = `
  mt-2 w-full rounded-lg
  border border-slate-300
  px-3 py-2.5 text-slate-900
  outline-none transition
  placeholder:text-slate-400
  focus:border-blue-500
  focus:ring-4
  focus:ring-blue-100
`;

export default function SignupForm() {
  const router = useRouter();

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
  } = useForm<SignupFormValues>({
    resolver: zodResolver(
      signupSchema,
    ),

    defaultValues: {
      business_scope: "mixed",
      organization_name: "",
      organization_email: "",
      phone: "",
      first_name: "",
      last_name: "",
      email: "",
      password: "",
      confirm_password: "",
    },
  });

  async function onSubmit(
    values: SignupFormValues,
  ): Promise<void> {
    setServerError(null);

    try {
      await signup({
        business_scope: values.business_scope,
        organization_name:
          values.organization_name,

        organization_email:
          values.organization_email,

        phone:
          values.phone || undefined,

        first_name:
          values.first_name,

        last_name:
          values.last_name,

        email:
          values.email,

        password:
          values.password,
      });

      router.push(
        "/login?signup=success",
      );

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
        "Unable to create your organization. Please try again.",
      );
    }
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
      <label className="block mb-5">Business scope<SearchSelect className="nx-input" {...register("business_scope")}><option value="mixed">Mixed / other</option><option value="retailer">Retail / shop</option><option value="wholesaler">Wholesale / distribution</option><option value="labour_supply">Labour supply / staffing</option><option value="manufacturer">Manufacturing business</option><option value="services">Professional services</option><option value="construction">Construction / contracting</option></SearchSelect></label>
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
          Create organization
        </h1>

        <p
          className="
            mt-2 text-sm text-slate-600
          "
        >
          Create your organization and
          administrator account.
        </p>
      </div>

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

      <div
        className="
          border-b border-slate-200 pb-2
        "
      >
        <h2
          className="
            font-semibold text-slate-900
          "
        >
          Organization details
        </h2>
      </div>

      <div>
        <label
          htmlFor="organization_name"
          className="
            block text-sm font-medium
            text-slate-700
          "
        >
          Organization name
        </label>

        <input
          id="organization_name"
          type="text"
          autoComplete="organization"
          {...register(
            "organization_name",
          )}
          className={inputClassName}
          placeholder="ABC Enterprises"
        />

        {errors.organization_name && (
          <p
            className="
              mt-1.5 text-sm text-red-600
            "
          >
            {
              errors
                .organization_name
                .message
            }
          </p>
        )}
      </div>

      <div>
        <label
          htmlFor="organization_email"
          className="
            block text-sm font-medium
            text-slate-700
          "
        >
          Organization email
        </label>

        <input
          id="organization_email"
          type="email"
          autoComplete="email"
          {...register(
            "organization_email",
          )}
          className={inputClassName}
          placeholder="accounts@example.com"
        />

        {errors.organization_email && (
          <p
            className="
              mt-1.5 text-sm text-red-600
            "
          >
            {
              errors
                .organization_email
                .message
            }
          </p>
        )}
      </div>

      <div>
        <label
          htmlFor="phone"
          className="
            block text-sm font-medium
            text-slate-700
          "
        >
          Phone
          <span className="text-slate-400">
            {" "}(optional)
          </span>
        </label>

        <input
          id="phone"
          type="tel"
          autoComplete="tel"
          {...register("phone")}
          className={inputClassName}
          placeholder="9876543210"
        />

        {errors.phone && (
          <p
            className="
              mt-1.5 text-sm text-red-600
            "
          >
            {errors.phone.message}
          </p>
        )}
      </div>

      <div
        className="
          border-b border-slate-200 pb-2
        "
      >
        <h2
          className="
            font-semibold text-slate-900
          "
        >
          Administrator details
        </h2>
      </div>

      <div
        className="
          grid gap-4 sm:grid-cols-2
        "
      >
        <div>
          <label
            htmlFor="first_name"
            className="
              block text-sm font-medium
              text-slate-700
            "
          >
            First name
          </label>

          <input
            id="first_name"
            type="text"
            autoComplete="given-name"
            {...register(
              "first_name",
            )}
            className={inputClassName}
            placeholder="Nitin"
          />

          {errors.first_name && (
            <p
              className="
                mt-1.5 text-sm text-red-600
              "
            >
              {
                errors
                  .first_name
                  .message
              }
            </p>
          )}
        </div>

        <div>
          <label
            htmlFor="last_name"
            className="
              block text-sm font-medium
              text-slate-700
            "
          >
            Last name
          </label>

          <input
            id="last_name"
            type="text"
            autoComplete="family-name"
            {...register(
              "last_name",
            )}
            className={inputClassName}
            placeholder="Vishwakarma"
          />

          {errors.last_name && (
            <p
              className="
                mt-1.5 text-sm text-red-600
              "
            >
              {
                errors
                  .last_name
                  .message
              }
            </p>
          )}
        </div>
      </div>

      <div>
        <label
          htmlFor="email"
          className="
            block text-sm font-medium
            text-slate-700
          "
        >
          Administrator email
        </label>

        <input
          id="email"
          type="email"
          autoComplete="email"
          {...register("email")}
          className={inputClassName}
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
        <label
          htmlFor="password"
          className="
            block text-sm font-medium
            text-slate-700
          "
        >
          Password
        </label>

        <input
          id="password"
          type="password"
          autoComplete="new-password"
          {...register("password")}
          className={inputClassName}
          placeholder="Create a password"
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

      <div>
        <label
          htmlFor="confirm_password"
          className="
            block text-sm font-medium
            text-slate-700
          "
        >
          Confirm password
        </label>

        <input
          id="confirm_password"
          type="password"
          autoComplete="new-password"
          {...register(
            "confirm_password",
          )}
          className={inputClassName}
          placeholder="Repeat your password"
        />

        {errors.confirm_password && (
          <p
            className="
              mt-1.5 text-sm text-red-600
            "
          >
            {
              errors
                .confirm_password
                .message
            }
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
          ? "Creating organization..."
          : "Create organization"}
      </button>

      <p
        className="
          text-center text-sm text-slate-600
        "
      >
        Already have an account?{" "}

        <Link
          href="/login"
          className="
            font-semibold text-blue-600
            hover:text-blue-700
          "
        >
          Sign in
        </Link>
      </p>
    </form>
  );
}