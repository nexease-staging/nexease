"use client";
import {useState} from "react";
import {useMutation,useQuery} from "@tanstack/react-query";
import {createCategory} from "@/features/categories/api";
import {listProductCategories} from "@/features/products/api";

export default function ItemCategory({value,onChange}:{value:string;onChange:(value:string)=>void}){
  const [adding,setAdding]=useState(false),[name,setName]=useState("");
  const categories=useQuery({queryKey:["invoice-item-categories"],queryFn:listProductCategories});
  const save=useMutation({mutationFn:()=>createCategory({name:name.trim()}),onSuccess:async category=>{
    onChange(category.name);setAdding(false);setName("");await categories.refetch();
  }});
  return <div className="space-y-1"><label>New item category<select className="nx-input" value={value} onChange={e=>onChange(e.target.value)}>
    <option value="">Pending review</option>{categories.data?.categories.map(c=><option key={c.id} value={c.name}>{c.name}</option>)}</select></label>
    <button type="button" className="nx-secondary" onClick={()=>setAdding(!adding)}>＋ Add category</button>
    {adding && <div><label>Category name<input className="nx-input" maxLength={100} value={name} onChange={e=>setName(e.target.value)}/></label>
    <button type="button" disabled={!name.trim()||save.isPending} onClick={()=>save.mutate()}>Create category</button>
    {save.error && <p role="alert">{save.error.message}</p>}</div>}</div>;
}
