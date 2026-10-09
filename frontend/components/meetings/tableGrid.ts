// One column template for the header and every row, so columns line up exactly.
// Phones: details + actions (date/time/duration move under the title). Tablet and up: the full table.
export const TABLE_GRID =
  "grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-3 " +
  "md:grid-cols-[minmax(0,1fr)_104px_84px_68px_64px] md:gap-x-4 " +
  "xl:grid-cols-[minmax(0,1fr)_140px_112px_96px_72px]";

// Shared horizontal padding: the table spans the content area like Fireflies'.
export const TABLE_PAD = "px-4 md:px-6 xl:pl-11 xl:pr-8";
