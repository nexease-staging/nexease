"use client";
import SearchSelect from "@/components/search-select";

import { apiRequest } from "@/lib/api/client";
import { exportWorkbook } from "@/features/business/workspace";
import {
 ChangeEvent,
 useRef,
 useState,
} from "react";
import {
 CheckCircle2,
 Database,
 FileSpreadsheet,
 History,
 RefreshCw,
 Upload,
} from "lucide-react";
import {
 DEFAULT_MIGRATION_SOURCE_SYSTEM,
 getMigrationTypeConfig,
 migrationTypeConfigs,
} from "@/features/migration/config";
import {
 useCreateMigration,
 useImportMigration,
 useMigrationList,
 useUploadMigrationFile,
 useValidateMigration,
} from "@/features/migration/hooks";
import type {
 MigrationStatus,
 MigrationType,
 MigrationUploadedFile,
} from "@/features/migration/types";
function getStatusClass(
 status: MigrationStatus,
): string {
 switch (status) {
  case "COMPLETED":
   return (
    "border-emerald-200 bg-emerald-50 "
    +
    "text-emerald-700"
   );
  case "COMPLETED_WITH_ERRORS":
   return (
    "border-amber-200 bg-amber-50 "
    +
    "text-amber-700"
   );
  case "FAILED":
   return (
    "border-red-200 bg-red-50 "
    +
    "text-red-700"
   );
  case "VALIDATING":
  case "IMPORTING":
   return (
    "border-blue-200 bg-blue-50 "
    +
    "text-blue-700"
   );
  default:
   return (
    "border-slate-200 bg-slate-100 "
    +
    "text-slate-600"
   );
 }
}
function formatStatus(
 status: MigrationStatus,
): string {
 return status
  .replaceAll("\\_", " ")
  .toLowerCase()
  .replace(
   /\b\w/g,
   (character) =>
    character.toUpperCase(),
  );
}
export default function DataMigrationPage() {
 const [
  migrationType,
  setMigrationType,
 ] = useState<MigrationType>(
  "INVENTORY",
 );
 const [fields,setFields]=useState<Record<string,{label:string;required:boolean}>>({});
 const [mapping,setMapping]=useState<Record<string,string>>({});
 const fileInputRef =
  useRef<HTMLInputElement | null>(
   null,
  );
 const [
  selectedFile,
  setSelectedFile,
 ] = useState<File | null>(
  null,
 );
 const [
  uploadedFile,
  setUploadedFile,
 ] = useState<
  MigrationUploadedFile | null
 >(
  null,
 );
 const [
  activeBatchId,
  setActiveBatchId,
 ] = useState<string | null>(
  null,
 );
 const [
  uploadError,
  setUploadError,
 ] = useState<string | null>(
  null,
 );
 const migrationQuery =
  useMigrationList(
   100,
  );
 const createMigration =
  useCreateMigration();
 const uploadMigration =
  useUploadMigrationFile();
 const validateMigration =
  useValidateMigration();
 const importMigration =
  useImportMigration();
 const uploadPending =
  createMigration.isPending
  ||
  uploadMigration.isPending;
 const selectedConfig =
  getMigrationTypeConfig(
   migrationType,
  );
 const migrations =
  migrationQuery.data
   ?.migrations
  ??
  [];
 const activeMigration =
  activeBatchId
   ? migrations.find(
     (migration) =>
      migration.id === activeBatchId,
    )
   : undefined;
 const workflowPending =
  validateMigration.isPending
  ||
  importMigration.isPending;
 function resetUpload(): void {
  setSelectedFile(
   null,
  );
  setUploadedFile(
   null,
  );
  setActiveBatchId(
   null,
  );
  setUploadError(
   null,
  );
  if (fileInputRef.current) {
   fileInputRef.current.value =
    "";
  }
 }
 function handleMigrationTypeChange(
  event: ChangeEvent<HTMLSelectElement>,
 ): void {
  setMigrationType(
   event.target
    .value as MigrationType,
  );
  resetUpload();
 }
 function handleFileChange(
  event: ChangeEvent<HTMLInputElement>,
 ): void {
  const file =
   event.target.files?.[0]
   ??
   null;
  setUploadError(
   null,
  );
  setUploadedFile(
   null,
  );
  setActiveBatchId(
   null,
  );
  if (!file) {
   setSelectedFile(
    null,
   );
   return;
  }
  const extension =
   file.name
    .split(".")
    .pop()
    ?.toLowerCase();
  if (
   extension !== "csv"
   &&
   extension !== "xlsx"
  ) {
   setSelectedFile(
    null,
   );
   setUploadError(
    "Select a CSV, XLSX file.",
   );
   event.target.value =
    "";
   return;
  }
  setSelectedFile(
   file,
  );
 }
 async function startUpload(): Promise<void> {
  if (!selectedFile) {
   setUploadError(
    "Select a migration file first.",
   );
   return;
  }
  setUploadError(
   null,
  );
  setUploadedFile(
   null,
  );
  try {
   const migration =
    await createMigration.mutateAsync({
     source_system:
      DEFAULT_MIGRATION_SOURCE_SYSTEM,
     migration_type:
      migrationType,
    });
   setActiveBatchId(
    migration.id,
   );
   const result =
    await uploadMigration.mutateAsync({
     batchId:
      migration.id,
     file:
      selectedFile,
    });
   setUploadedFile(result.file);
   const details=await apiRequest<{schema:{fields:Record<string,{label:string;required:boolean}>};mapping:Record<string,string>}>(`/migrations/${migration.id}/mapping/`);
   setFields(details.data.schema.fields);setMapping(details.data.mapping);

   setActiveBatchId(
    result.migration.id,
   );
  } catch (error) {
   setUploadError(
    error instanceof Error
     ? error.message
     : (
      "Unable to upload "
      +
      "migration file."
     ),
   );
  }
 }
 async function startValidation(): Promise<void> {
  if (!activeBatchId) {
   setUploadError(
    "Upload a migration file first.",
   );
   return;
  }
  setUploadError(
   null,
  );
  try {
   await apiRequest(`/migrations/${activeBatchId}/mapping/`,{method:"PATCH",body:{mapping}});
   await validateMigration.mutateAsync(
    activeBatchId,
   );
   await migrationQuery.refetch();
  } catch (error) {
   setUploadError(
    error instanceof Error
     ? error.message
     : "Unable to validate migration.",
   );
  }
 }
 async function startImport(): Promise<void> {
  if (!activeBatchId) {
   setUploadError(
    "Validate a migration first.",
   );
   return;
  }
  setUploadError(
   null,
  );
  try {
   await importMigration.mutateAsync(
    activeBatchId,
   );
   await migrationQuery.refetch();
  } catch (error) {
   setUploadError(
    error instanceof Error
     ? error.message
     : "Unable to import migration.",
   );
  }
 }
 return (
  <section className="space-y-6">
<section className="nx-panel mb-5"><button type="button" className="nx-button" onClick={()=>exportWorkbook(`/migrations/templates/${migrationType}/`,`NexEase-${migrationType}.xlsx`).catch(e=>setUploadError(e.message))}>Click here to download a sample Excel template</button><p className="text-sm text-slate-500 mt-3">Fill the Data sheet using the included column guide. Import master data first, then transactions.</p></section>
{uploadedFile&&<section className="nx-panel mb-5"><h2 className="text-xl font-semibold mb-4">Map file columns</h2><p className="text-sm mb-4">Choose the source column for each target. Leave Auto detect to use recognised column names.</p><div className="grid md:grid-cols-3 gap-4">{Object.entries(fields).map(([key,field])=><label key={key}>{field.label}{field.required?" *":""}<SearchSelect className="nx-input" value={mapping[key]??""} onChange={e=>setMapping({...mapping,[key]:e.target.value})}><option value="">Auto detect</option>{uploadedFile.columns.map(c=><option key={c}>{c}</option>)}</SearchSelect></label>)}</div></section>}

   <div
    className="
     flex flex-col gap-4
     sm:flex-row
     sm:items-center
     sm:justify-between
    "
   >
    <div>
     <div
      className="
       flex items-center gap-2
      "
     >
      <Database
       size={25}
       className="text-blue-600"
      />
      <h1
       className="
        text-2xl font-bold
        text-slate-900
       "
      >
       Data Migration
      </h1>
     </div>
     <p
      className="
       mt-1 max-w-2xl
       text-sm text-slate-600
      "
     >
      Import master data,
      opening inventory, and
      historical transactions
      into your organization.
     </p>
    </div>
    <button
     type="button"
     disabled={
      migrationQuery.isFetching
     }
     onClick={() => {
      void migrationQuery.refetch();
     }}
     className="
      inline-flex items-center
      justify-center gap-2
      rounded-lg border
      border-slate-300
      bg-white px-4 py-2
      text-sm font-semibold
      text-slate-700
      hover:bg-slate-50
      disabled:cursor-not-allowed
      disabled:opacity-50
     "
    >
     <RefreshCw
      size={16}
      className={
       migrationQuery.isFetching
        ? "animate-spin"
        : undefined
      }
     />
     Refresh
    </button>
   </div>
   <div
    className="
     grid gap-6
     xl:grid-cols-[minmax(0,1fr)\\_360px]
    "
   >
    <div
     className="
      rounded-2xl border
      border-slate-200
      bg-white p-5
      shadow-sm
     "
    >
     <div
      className="
       flex items-center gap-2
      "
     >
      <Upload
       size={20}
       className="text-blue-600"
      />
      <h2
       className="
        text-lg font-semibold
        text-slate-900
       "
      >
       Start migration
      </h2>
     </div>
     <p
      className="
       mt-1 text-sm
       text-slate-500
      "
     >
      Select the type of data
      you want to migrate.
     </p>
     <label
      className="
       mt-5 block space-y-1.5
      "
     >
      <span
       className="
        text-sm font-semibold
        text-slate-700
       "
      >
       Migration type
      </span>
      <SearchSelect
       value={migrationType}
       disabled={uploadPending || workflowPending}
       onChange={
        handleMigrationTypeChange
       }
       className="
        h-11 w-full
        rounded-lg border
        border-slate-300
        bg-white px-3
        text-sm text-slate-900
        outline-none
        focus:border-blue-500
        focus:ring-2
        focus:ring-blue-100
        disabled:cursor-not-allowed
        disabled:bg-slate-100
        disabled:opacity-70
       "
      >
       {migrationTypeConfigs.map(
        (config) => (
         <option
          key={config.type}
          value={config.type}
         >
          {config.label}
         </option>
        ),
       )}
      </SearchSelect>
     </label>
     <div
      className="
       mt-5 rounded-xl
       border border-blue-100
       bg-blue-50 p-4
      "
     >
      <div
       className="
        flex items-start gap-3
       "
      >
       <FileSpreadsheet
        size={21}
        className="
         mt-0.5 shrink-0
         text-blue-600
        "
       />
       <div>
        <h3
         className="
          font-semibold
          text-slate-900
         "
        >
         {selectedConfig.label}
        </h3>
        <p
         className="
          mt-1 text-sm
          text-slate-600
         "
        >
         {
          selectedConfig
           .description
         }
        </p>
       </div>
      </div>
      <div className="mt-4">
       <p
        className="
         text-xs font-semibold
         uppercase tracking-wide
         text-slate-500
        "
       >
        Required columns
       </p>
       {
        selectedConfig
         .requiredColumns
         .length > 0
         ? (
          <div
           className="
            mt-2 flex
            flex-wrap gap-2
           "
          >
           {
            selectedConfig
             .requiredColumns
             .map(
              (column) => (
               <span
                key={column}
                className="
                 inline-flex
                 items-center
                 gap-1.5
                 rounded-full
                 border
                 border-blue-200
                 bg-white
                 px-2.5 py-1
                 text-xs
                 font-semibold
                 text-blue-700
                "
               >
                <CheckCircle2
                 size={13}
                />
                {column}
               </span>
              ),
             )
           }
          </div>
         )
         : (
          <p
           className="
            mt-2 text-sm
            text-slate-600
           "
          >
           Column requirements
           will be validated by
           the migration service.
          </p>
         )
       }
      </div>
     </div>
     <div
      className="
       mt-5 rounded-xl
       border border-dashed
       border-slate-300
       bg-slate-50
       px-6 py-8
       text-center
      "
     >
      <input
       ref={fileInputRef}
       type="file"
       accept=".csv,.xlsx"
       onChange={
        handleFileChange
       }
       className="hidden"
      />
      <Upload
       size={32}
       className="
        mx-auto text-slate-400
       "
      />
      <h3
       className="
        mt-3 font-semibold
        text-slate-900
       "
      >
       Upload migration file
      </h3>
      <p
       className="
        mx-auto mt-1
        max-w-md text-sm
        text-slate-500
       "
      >
       Select a CSV or Excel
       file containing your{" "}
       {selectedConfig.label
        .toLowerCase()}{" "}
       data.
      </p>
      <button
       type="button"
       disabled={uploadPending || workflowPending}
       onClick={() => {
        fileInputRef
         .current
         ?.click();
       }}
       className="
        mt-4 inline-flex
        items-center gap-2
        rounded-lg border
        border-slate-300
        bg-white px-4 py-2
        text-sm font-semibold
        text-slate-700
        hover:bg-slate-100
        disabled:cursor-not-allowed
        disabled:opacity-50
       "
      >
       <FileSpreadsheet
        size={16}
       />
       Choose file
      </button>
      {selectedFile ? (
       <div
        className="
         mx-auto mt-4
         max-w-lg
         rounded-lg border
         border-slate-200
         bg-white p-3
         text-left
        "
       >
        <p
         className="
          truncate text-sm
          font-semibold
          text-slate-900
         "
        >
         {selectedFile.name}
        </p>
        <p
         className="
          mt-1 text-xs
          text-slate-500
         "
        >
         {(
          selectedFile.size
          /
          1024
         ).toFixed(1)}{" "}
         KB
        </p>
       </div>
      ) : null}
      {selectedFile ? (
       <button
        type="button"
        disabled={uploadPending || workflowPending}
        onClick={() => {
         void startUpload();
        }}
        className="
         mt-4 inline-flex
         items-center gap-2
         rounded-lg
         bg-blue-600
         px-5 py-2.5
         text-sm font-semibold
         text-white
         hover:bg-blue-700
         disabled:cursor-not-allowed
         disabled:opacity-50
        "
       >
        {uploadPending ? (
         <RefreshCw
          size={16}
          className="animate-spin"
         />
        ) : (
         <Upload size={16} />
        )}
        {
         createMigration.isPending
          ? "Creating batch..."
          : (
           uploadMigration.isPending
            ? "Uploading..."
            : "Upload file"
          )
        }
       </button>
      ) : null}
     </div>
     {uploadError ? (
      <div
       className="
        mt-4 rounded-xl
        border border-red-200
        bg-red-50 px-4 py-3
        text-sm text-red-700
       "
      >
       {uploadError}
      </div>
     ) : null}
     {uploadedFile ? (
      <div
       className="
        mt-4 rounded-xl
        border
        border-emerald-200
        bg-emerald-50 p-4
       "
      >
       <div
        className="
         flex items-start gap-3
        "
       >
        <CheckCircle2
         size={22}
         className="
          mt-0.5 shrink-0
          text-emerald-600
         "
        />
        <div className="min-w-0">
         <h3
          className="
           font-semibold
           text-emerald-900
          "
         >
          File uploaded
          successfully
         </h3>
         <p
          className="
           mt-1 break-all
           text-sm
           text-emerald-800
          "
         >
          {uploadedFile.filename}
         </p>
        </div>
       </div>
       <div
        className="
         mt-4 grid gap-3
         sm:grid-cols-3
        "
       >
        <div
         className="
          rounded-lg
          bg-white p-3
         "
        >
         <p
          className="
           text-xs
           font-semibold
           uppercase
           text-slate-500
          "
         >
          Rows
         </p>
         <p
          className="
           mt-1 font-bold
           text-slate-900
          "
         >
          {
           uploadedFile
            .total_rows
          }
         </p>
        </div>
        <div
         className="
          rounded-lg
          bg-white p-3
         "
        >
         <p
          className="
           text-xs
           font-semibold
           uppercase
           text-slate-500
          "
         >
          Columns
         </p>
         <p
          className="
           mt-1 font-bold
           text-slate-900
          "
         >
          {
           uploadedFile
            .columns
            .length
          }
         </p>
        </div>
        <div
         className="
          rounded-lg
          bg-white p-3
         "
        >
         <p
          className="
           text-xs
           font-semibold
           uppercase
           text-slate-500
          "
         >
          Format
         </p>
         <p
          className="
           mt-1 font-bold
           uppercase
           text-slate-900
          "
         >
          {
           uploadedFile
            .extension
          }
         </p>
        </div>
       </div>
       {
        uploadedFile
         .columns
         .length > 0
         ? (
          <div className="mt-4">
           <p
            className="
             text-xs
             font-semibold
             uppercase
             tracking-wide
             text-emerald-800
            "
           >
            Detected columns
           </p>
           <div
            className="
             mt-2 flex
             flex-wrap gap-2
            "
           >
            {
             uploadedFile
              .columns
              .map(
               (column) => (
                <span
                 key={column}
                 className="
                  rounded-full
                  border
                  border-emerald-200
                  bg-white
                  px-2.5 py-1
                  text-xs
                  font-semibold
                  text-emerald-700
                 "
                >
                 {column}
                </span>
               ),
              )
            }
           </div>
          </div>
         )
         : null
       }
       {activeBatchId ? (
        <p
         className="
          mt-4 break-all
          text-xs
          text-emerald-700
         "
        >
         Batch ID:{" "}
         {activeBatchId}
        </p>
       ) : null}
       {activeMigration ? (
        <div
         className="
          mt-4 rounded-xl border
          border-emerald-200
          bg-white p-4
         "
        >
         <div
          className="
           flex flex-col gap-3
           sm:flex-row
           sm:items-center
           sm:justify-between
          "
         >
          <div>
           <p
            className="
             text-sm font-semibold
             text-slate-900
            "
           >
            Migration workflow
           </p>
           <p
            className="
             mt-1 text-sm
             text-slate-600
            "
           >
            Current status:{" "}
            <span className="font-semibold">
             {formatStatus(
              activeMigration.status,
             )}
            </span>
           </p>
          </div>
          {activeMigration.status === "UPLOADED" ? (
           <button
            type="button"
            disabled={workflowPending}
            onClick={() => {
             void startValidation();
            }}
            className="
             inline-flex items-center
             justify-center gap-2
             rounded-lg bg-blue-600
             px-4 py-2.5
             text-sm font-semibold
             text-white
             hover:bg-blue-700
             disabled:cursor-not-allowed
             disabled:opacity-50
            "
           >
            {validateMigration.isPending ? (
             <RefreshCw
              size={16}
              className="animate-spin"
             />
            ) : (
             <CheckCircle2 size={16} />
            )}
            {validateMigration.isPending
             ? "Validating..."
             : "Validate migration"}
           </button>
          ) : null}
          {activeMigration.status === "VALIDATED" ? (
           <button
            type="button"
            disabled={
             workflowPending
             ||
             activeMigration.invalid_rows > 0
             ||
             activeMigration.valid_rows === 0
            }
            onClick={() => {
             void startImport();
            }}
            className="
             inline-flex items-center
             justify-center gap-2
             rounded-lg bg-emerald-600
             px-4 py-2.5
             text-sm font-semibold
             text-white
             hover:bg-emerald-700
             disabled:cursor-not-allowed
             disabled:opacity-50
            "
           >
            {importMigration.isPending ? (
             <RefreshCw
              size={16}
              className="animate-spin"
             />
            ) : (
             <Database size={16} />
            )}
            {importMigration.isPending
             ? "Importing..."
             : "Import migration"}
           </button>
          ) : null}
         </div>
         <div
          className="
           mt-4 grid gap-3
           sm:grid-cols-4
          "
         >
          {[
           ["Total", activeMigration.total_rows],
           ["Valid", activeMigration.valid_rows],
           ["Invalid", activeMigration.invalid_rows],
           ["Imported", activeMigration.imported_rows],
          ].map(([label, value]) => (
           <div
            key={String(label)}
            className="
             rounded-lg bg-slate-50
             p-3
            "
           >
            <p
             className="
              text-xs font-semibold
              uppercase text-slate-500
             "
            >
             {label}
            </p>
            <p
             className="
              mt-1 text-lg font-bold
              text-slate-900
             "
            >
             {value}
            </p>
           </div>
          ))}
         </div>
         {activeMigration.status === "VALIDATED"
         && activeMigration.invalid_rows > 0 ? (
          <p
           className="
            mt-3 rounded-lg
            border border-amber-200
            bg-amber-50 px-3 py-2
            text-sm text-amber-800
           "
          >
           Validation found invalid rows.
           Correct the source data and upload
           a new migration file before importing.
          </p>
         ) : null}
         {activeMigration.status === "COMPLETED" ? (
          <p
           className="
            mt-3 rounded-lg
            border border-emerald-200
            bg-emerald-50 px-3 py-2
            text-sm font-semibold
            text-emerald-800
           "
          >
           Migration completed successfully.
          </p>
         ) : null}
         {activeMigration.status ===
          "COMPLETED_WITH_ERRORS" ? (
          <p
           className="
            mt-3 rounded-lg
            border border-amber-200
            bg-amber-50 px-3 py-2
            text-sm text-amber-800
           "
          >
           Migration completed with failed rows.
           Review the migration history before
           continuing.
          </p>
         ) : null}
        </div>
       ) : null}
      </div>
     ) : null}
    </div>
    <div
     className="
      rounded-2xl border
      border-slate-200
      bg-white p-5
      shadow-sm
     "
    >
     <div
      className="
       flex items-center gap-2
      "
     >
      <History
       size={20}
       className="text-blue-600"
      />
      <h2
       className="
        text-lg font-semibold
        text-slate-900
       "
      >
       Migration summary
      </h2>
     </div>
     <div
      className="
       mt-5 grid
       grid-cols-2 gap-3
      "
     >
      <div
       className="
        rounded-xl
        bg-slate-50 p-4
       "
      >
       <p
        className="
         text-xs font-semibold
         uppercase
         text-slate-500
        "
       >
        Total
       </p>
       <p
        className="
         mt-1 text-2xl
         font-bold
         text-slate-900
        "
       >
        {migrations.length}
       </p>
      </div>
      <div
       className="
        rounded-xl
        bg-emerald-50 p-4
       "
      >
       <p
        className="
         text-xs font-semibold
         uppercase
         text-emerald-600
        "
       >
        Completed
       </p>
       <p
        className="
         mt-1 text-2xl
         font-bold
         text-emerald-700
        "
       >
        {
         migrations.filter(
          (migration) =>
           migration.status
           ===
           "COMPLETED",
         ).length
        }
       </p>
      </div>
     </div>
     <div
      className="
       mt-4 rounded-xl
       border border-slate-200
       p-4
      "
     >
      <p
       className="
        text-sm font-semibold
        text-slate-900
       "
      >
       Recommended order
      </p>
      <ol
       className="
        mt-3 space-y-2
        text-sm text-slate-600
       "
      >
       <li>
        1. Categories
       </li>
       <li>
        2. Products
       </li>
       <li>
        3. Warehouses
       </li>
       <li>
        4. Opening Inventory
       </li>
       <li>
        5. Customers and
        suppliers
       </li>
       <li>
        6. Historical
        transactions
       </li>
      </ol>
     </div>
    </div>
   </div>
   <div
    className="
     overflow-hidden
     rounded-2xl border
     border-slate-200
     bg-white shadow-sm
    "
   >
    <div
     className="
      flex items-center
      justify-between
      border-b
      border-slate-200
      px-5 py-4
     "
    >
     <div>
      <h2
       className="
        font-semibold
        text-slate-900
       "
      >
       Migration history
      </h2>
      <p
       className="
        mt-0.5 text-sm
        text-slate-500
       "
      >
       Recent migration batches.
      </p>
     </div>
    </div>
    {
     migrationQuery.isPending
      ? (
       <div
        className="
         flex min-h-48
         items-center
         justify-center
         text-sm
         text-slate-500
        "
       >
        Loading migrations...
       </div>
      )
      : migrationQuery.isError
       ? (
        <div
         className="
          flex min-h-48
          flex-col
          items-center
          justify-center
          gap-3 p-6
          text-center
         "
        >
         <p
          className="
           text-sm
           font-medium
           text-red-700
          "
         >
          {
           migrationQuery
            .error
            .message
          }
         </p>
         <button
          type="button"
          onClick={() => {
           void migrationQuery
            .refetch();
          }}
          className="
           rounded-lg
           bg-slate-900
           px-4 py-2
           text-sm
           font-semibold
           text-white
           hover:bg-slate-700
          "
         >
          Try again
         </button>
        </div>
       )
       : migrations.length === 0
        ? (
         <div
          className="
           flex min-h-48
           flex-col
           items-center
           justify-center
           p-6 text-center
          "
         >
          <History
           size={34}
           className="
            text-slate-300
           "
          />
          <h3
           className="
            mt-3
            font-semibold
            text-slate-900
           "
          >
           No migrations yet
          </h3>
          <p
           className="
            mt-1 text-sm
            text-slate-500
           "
          >
           Your migration
           batches will
           appear here.
          </p>
         </div>
        )
        : (
         <div
          className="
           overflow-x-auto
          "
         >
          <table
           className="
            min-w-full
            divide-y
            divide-slate-200
           "
          >
           <thead
            className="
             bg-slate-50
            "
           >
            <tr>
             {[
              "Type",
              "Source",
              "Status",
              "Rows",
              "Imported",
              "Failed",
             ].map(
              (heading) => (
               <th
                key={
                 heading
                }
                scope="col"
                className="
                 whitespace-nowrap
                 px-4 py-3
                 text-left
                 text-xs
                 font-semibold
                 uppercase
                 tracking-wide
                 text-slate-500
                "
               >
                {heading}
               </th>
              ),
             )}
            </tr>
           </thead>
           <tbody
            className="
             divide-y
             divide-slate-100
            "
           >
            {
             migrations.map(
              (
               migration,
              ) => (
               <tr
                key={
                 migration.id
                }
                className="
                 hover:bg-slate-50
                "
               >
                <td
                 className="
                  whitespace-nowrap
                  px-4 py-4
                  text-sm
                  font-semibold
                  text-slate-900
                 "
                >
                 {
                  getMigrationTypeConfig(
                   migration
                    .migration_type,
                  ).label
                 }
                </td>
                <td
                 className="
                  whitespace-nowrap
                  px-4 py-4
                  text-sm
                  text-slate-600
                 "
                >
                 {
                  migration
                   .source_system
                 }
                </td>
                <td
                 className="
                  whitespace-nowrap
                  px-4 py-4
                 "
                >
                 <span
                  className={`
                  inline-flex
                  rounded-full
                  border
                  px-2.5 py-1
                  text-xs
                  font-semibold
                  ${getStatusClass(
                    migration.status,
                  )}
                  `}
                 >
                  {
                   formatStatus(
                    migration
                     .status,
                   )
                  }
                 </span>
                </td>
                <td
                 className="
                  px-4 py-4
                  text-sm
                  text-slate-600
                 "
                >
                 {
                  migration
                   .total_rows
                 }
                </td>
                <td
                 className="
                  px-4 py-4
                  text-sm
                  font-semibold
                  text-emerald-700
                 "
                >
                 {
                  migration
                   .imported_rows
                 }
                </td>
                <td
                 className="
                  px-4 py-4
                  text-sm
                  font-semibold
                  text-red-700
                 "
                >
                 {
                  migration
                   .failed_rows
                 }
                </td>
               </tr>
              ),
             )
            }
           </tbody>
          </table>
         </div>
        )
    }
   </div>
  </section>
 );
}
