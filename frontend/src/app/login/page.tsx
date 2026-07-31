"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { AxiosError } from "axios";
import { Search } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { login } from "@/lib/auth-api";
import { setToken } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Field,
  FieldError,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field";
import { Input } from "@/components/ui/input";

const loginSchema = z.object({
  username: z.string().min(1, "اكتب اسم المستخدم"),
  password: z.string().min(1, "اكتب كلمة المرور"),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const router = useRouter();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  });

  const mutation = useMutation({
    mutationFn: login,
    onSuccess: (data) => {
      setToken(data.access_token);
      router.push("/");
    },
  });

  const onSubmit = handleSubmit((values) => {
    mutation.mutate(values);
  });

  const serverError =
    mutation.error instanceof AxiosError
      ? mutation.error.response?.status === 401
        ? "اسم المستخدم أو كلمة المرور غلط"
        : "حصل خطأ، جرب تاني"
      : undefined;

  return (
    <div className="flex flex-1 items-center justify-center bg-background p-4">
      <Card className="w-full max-w-sm">
        <CardHeader className="items-center text-center">
          <div className="mb-2 flex size-12 items-center justify-center rounded-xl bg-primary">
            <Search className="size-6 text-primary-foreground" />
          </div>
          <CardTitle className="text-xl">SmartHunt</CardTitle>
          <CardDescription>سجّل دخولك للمتابعة</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} noValidate>
            <FieldGroup>
              <Field>
                <FieldLabel htmlFor="username">اسم المستخدم</FieldLabel>
                <Input
                  id="username"
                  autoComplete="username"
                  autoFocus
                  {...register("username")}
                />
                <FieldError errors={[errors.username]} />
              </Field>

              <Field>
                <FieldLabel htmlFor="password">كلمة المرور</FieldLabel>
                <Input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  {...register("password")}
                />
                <FieldError errors={[errors.password]} />
              </Field>

              {serverError && (
                <p role="alert" className="text-sm text-destructive">
                  {serverError}
                </p>
              )}

              <Button type="submit" disabled={mutation.isPending}>
                {mutation.isPending ? "جاري الدخول..." : "دخول"}
              </Button>

              <p className="text-center text-sm text-muted-foreground">
                لسه معملتش حساب؟{" "}
                <Link href="/register" className="underline">
                  إنشاء حساب
                </Link>
              </p>
            </FieldGroup>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
