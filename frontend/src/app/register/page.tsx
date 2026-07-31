"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { AxiosError } from "axios";
import { Search } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { login, register as registerAccount } from "@/lib/auth-api";
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

const registerSchema = z.object({
  username: z.string().min(3, "3 حروف على الأقل"),
  email: z.string().email("إيميل غير صحيح"),
  password: z.string().min(8, "8 حروف على الأقل"),
});

type RegisterFormValues = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const router = useRouter();

  const {
    register: registerField,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
  });

  const mutation = useMutation({
    mutationFn: async (values: RegisterFormValues) => {
      await registerAccount(values);
      return login({ username: values.username, password: values.password });
    },
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
      ? mutation.error.response?.status === 400
        ? "اسم المستخدم أو الإيميل ده مستخدم قبل كده"
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
          <CardDescription>إنشاء حساب المالك</CardDescription>
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
                  {...registerField("username")}
                />
                <FieldError errors={[errors.username]} />
              </Field>

              <Field>
                <FieldLabel htmlFor="email">الإيميل</FieldLabel>
                <Input
                  id="email"
                  type="email"
                  autoComplete="email"
                  {...registerField("email")}
                />
                <FieldError errors={[errors.email]} />
              </Field>

              <Field>
                <FieldLabel htmlFor="password">كلمة المرور</FieldLabel>
                <Input
                  id="password"
                  type="password"
                  autoComplete="new-password"
                  {...registerField("password")}
                />
                <FieldError errors={[errors.password]} />
              </Field>

              {serverError && (
                <p role="alert" className="text-sm text-destructive">
                  {serverError}
                </p>
              )}

              <Button type="submit" disabled={mutation.isPending}>
                {mutation.isPending ? "جاري الإنشاء..." : "إنشاء الحساب"}
              </Button>

              <p className="text-center text-sm text-muted-foreground">
                عندك حساب بالفعل؟{" "}
                <Link href="/login" className="underline">
                  دخول
                </Link>
              </p>
            </FieldGroup>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
