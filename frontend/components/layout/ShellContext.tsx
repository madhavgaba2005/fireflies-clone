"use client";

import { createContext, useContext } from "react";

/** Lets page-level toolbars (e.g. the meeting toolbar) open the phone navigation drawer. */
export const OpenNavDrawerContext = createContext<() => void>(() => {});

export const useOpenNavDrawer = () => useContext(OpenNavDrawerContext);
