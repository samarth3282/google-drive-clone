import React from "react";

const Loading = () => {
  return (
    <div className="page-container">
      <section className="w-full">
        <div className="h-10 w-48 animate-pulse rounded-md bg-light-200" />

        <div className="total-size-section">
          <div className="h-6 w-32 animate-pulse rounded-md bg-light-200" />
          <div className="h-10 w-40 animate-pulse rounded-md bg-light-200" />
        </div>
      </section>

      {/* Loading skeleton for files */}
      <section className="file-list">
        {[...Array(6)].map((_, index) => (
          <div
            key={index}
            className="flex h-[200px] flex-col gap-3 rounded-[18px] border border-light-100 p-5"
          >
            <div className="h-[120px] w-full animate-pulse rounded-md bg-light-200" />
            <div className="space-y-2">
              <div className="h-4 w-3/4 animate-pulse rounded bg-light-200" />
              <div className="h-3 w-1/2 animate-pulse rounded bg-light-200" />
            </div>
          </div>
        ))}
      </section>
    </div>
  );
};

export default Loading;
