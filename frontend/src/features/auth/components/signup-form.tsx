"use client";
import {useState} from "react";
import Link from "next/link";
import {useRouter} from "next/navigation";
import {useForm} from "react-hook-form";
import {zodResolver} from "@hookform/resolvers/zod";
import {z} from "zod";
import {Building2, MessageCircle, Save} from "lucide-react";
import {APIRequestError} from "@/lib/api/client";
import {signup} from "@/features/auth/api";
import SearchSelect from "@/components/search-select";
const signupSchema = z
  .object({
    business_scope: z.string().min(1),
    address: z.string().max(500).optional(),
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


export default function SignupForm(){
 const router=useRouter();
 const [serverError,setServerError]=useState<string|null>(null);
 const {register,handleSubmit,formState:{errors,isSubmitting}}=useForm<SignupFormValues>({
  resolver:zodResolver(signupSchema),
  defaultValues:{business_scope:"mixed",organization_name:"",organization_email:"",phone:"",address:"",first_name:"",last_name:"",email:"",password:"",confirm_password:""}
 });
 async function onSubmit(values:SignupFormValues){
  setServerError(null);
  try{await signup({
   business_scope:values.business_scope,organization_name:values.organization_name,
   organization_email:values.organization_email,phone:values.phone||undefined,address:values.address||undefined,
   first_name:values.first_name,last_name:values.last_name,email:values.email,password:values.password
  });router.push("/login?signup=success")}
  catch(error){setServerError(error instanceof APIRequestError?error.message:"Unable to create your organisation. Please try again.")}
 }
 const field=(name:Exclude<keyof SignupFormValues,"business_scope">,label:string,type="text",placeholder="",autoComplete?:string)=>
  <div className="nx-signup-row" key={name}><label htmlFor={name}>{label}</label><div>
   <input id={name} type={type} placeholder={placeholder} autoComplete={autoComplete} className="nx-input" {...register(name)} aria-invalid={!!errors[name]} aria-describedby={errors[name]?name+"-error":undefined}/>
   {errors[name]&&<p id={name+"-error"} className="nx-signup-error" role="alert">{errors[name]?.message}</p>}
  </div></div>;
 return <form onSubmit={handleSubmit(onSubmit)} className="nx-signup-form" noValidate>
  <header className="nx-signup-heading"><div><Link href="/" className="mb-2 flex items-center gap-2 text-sm font-semibold"><img src="/nexease-brand-icon.png" alt="" width="25" height="25"/>NexEase</Link><h1>Add your business</h1></div><a href="https://wa.me/919209753378" target="_blank" rel="noopener noreferrer"><MessageCircle size={20}/>Need help?</a></header>
  <div className="nx-signup-fields">
   {serverError&&<p role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{serverError}</p>}
   <h2 className="flex items-center gap-2"><Building2 size={17}/>Business information</h2>
   {field("organization_name","Company name *","text","ABC Enterprises","organization")}
   <div className="nx-signup-row"><label htmlFor="business_scope">Business type *</label><SearchSelect id="business_scope" className="nx-input" {...register("business_scope")}><option value="mixed">Mixed / other</option><option value="retailer">Retail / shop</option><option value="wholesaler">Wholesale / distribution</option><option value="labour_supply">Labour supply / staffing</option><option value="manufacturer">Manufacturing business</option><option value="services">Professional services</option><option value="construction">Construction / contracting</option></SearchSelect></div>
   {field("organization_email","Organisation email *","email","accounts@example.com","email")}
   {field("phone","Phone","tel","Business phone number","tel")}
   {field("address","Business address","text","Street, city, state and pincode","street-address")}
   <p className="text-xs leading-6 text-slate-500">After signing in, configure your GST registration and use GSTIN lookup from Taxation. A business without GST registration can also use NexEase.</p>
   <h2>Administrator account</h2>
   {field("first_name","First name *","text","Your first name","given-name")}
   {field("last_name","Last name *","text","Your last name","family-name")}
   {field("email","Login email *","email","you@example.com","username")}
   {field("password","Password *","password","At least 8 characters","new-password")}
   {field("confirm_password","Confirm password *","password","Re-enter password","new-password")}
   <p className="text-xs text-slate-500">Your login email and organisation email can be the same. Fields marked * are required.</p>
  </div>
  <footer className="nx-signup-footer"><Link href="/login">Already registered? Sign in</Link><button type="submit" disabled={isSubmitting} className="nx-button"><Save size={17}/>{isSubmitting?"Creating…":"Create organisation"}</button></footer>
 </form>;
}
