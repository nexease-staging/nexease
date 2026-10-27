function SkeletonBlock({
  className = "",
}: {
  className?: string;
}) {
  return (
    <div
      className={`
        animate-pulse
        rounded-lg
        bg-slate-200
        ${className}
      `}
    />
  );
}


export default function DashboardLoadingSkeleton() {
  return (
    <div
      aria-label="Loading dashboard"
      className="
        space-y-6
      "
    >
      <section
        className="
          grid
          gap-4
          sm:grid-cols-2
          xl:grid-cols-4
        "
      >
        {
          Array.from({
            length: 7,
          }).map(
            (
              _,
              index,
            ) => (
              <article
                key={
                  index
                }
                className={`
                  rounded-2xl
                  border
                  border-slate-200
                  bg-white
                  p-5
                  shadow-sm
                  ${
                    index === 6
                      ? "xl:col-span-2"
                      : ""
                  }
                `}
              >
                <div
                  className="
                    flex
                    items-start
                    justify-between
                    gap-4
                  "
                >
                  <div
                    className="
                      flex-1
                      space-y-3
                    "
                  >
                    <SkeletonBlock
                      className="
                        h-4
                        w-28
                      "
                    />

                    <SkeletonBlock
                      className="
                        h-8
                        w-36
                      "
                    />

                    <SkeletonBlock
                      className="
                        h-3
                        w-40
                      "
                    />
                  </div>

                  <SkeletonBlock
                    className="
                      h-11
                      w-11
                      rounded-xl
                    "
                  />
                </div>
              </article>
            ),
          )
        }
      </section>

      <section
        className="
          grid
          gap-6
          xl:grid-cols-2
        "
      >
        {
          Array.from({
            length: 2,
          }).map(
            (
              _,
              index,
            ) => (
              <article
                key={
                  index
                }
                className="
                  rounded-2xl
                  border
                  border-slate-200
                  bg-white
                  p-5
                  shadow-sm
                "
              >
                <SkeletonBlock
                  className="
                    h-5
                    w-32
                  "
                />

                <SkeletonBlock
                  className="
                    mt-2
                    h-3
                    w-44
                  "
                />

                <SkeletonBlock
                  className="
                    mt-6
                    h-72
                    w-full
                    rounded-xl
                  "
                />
              </article>
            ),
          )
        }
      </section>

      <article
        className="
          rounded-2xl
          border
          border-slate-200
          bg-white
          p-5
          shadow-sm
        "
      >
        <SkeletonBlock
          className="
            h-5
            w-48
          "
        />

        <SkeletonBlock
          className="
            mt-2
            h-3
            w-40
          "
        />

        <SkeletonBlock
          className="
            mt-6
            h-72
            w-full
            rounded-xl
          "
        />
      </article>
    </div>
  );
}