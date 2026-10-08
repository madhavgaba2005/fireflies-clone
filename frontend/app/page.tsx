import { redirect } from "next/navigation";

// Like Fireflies, the meetings library is the home view.
export default function Home() {
  redirect("/meetings");
}
