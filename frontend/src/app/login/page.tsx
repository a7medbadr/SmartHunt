"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { AxiosError } from "axios";
import { Search } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { login } from "@/lib/auth-api";
import { setToken } from "@/lib/auth";
import { useTranslation } from "@/lib/i18n/language-context";
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

type LoginFormValues = {
  username: string;
  password: string;
};

export default function LoginPage() {
  const router = useRouter();
  const { t } = useTranslation();

  const loginSchema = useMemo(
    () =>
      z.object({
        username: z.string().min(1, t("auth", "usernameRequired")),
        password: z.string().min(1, t("auth", "passwordRequired")),
      }),
    [t],
  );

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
        ? t("auth", "invalidCredentials")
        : t("auth", "genericError")
      : undefined;

  return (
    <div className="flex flex-1 items-center justify-center bg-background p-4">
      <Card className="w-full max-w-sm">
        <CardHeader className="items-center text-center">
          <div className="mb-2 flex size-12 items-center justify-center rounded-xl bg-primary">
            <Search className="size-6 text-primary-foreground" />
          </div>
          <CardTitle className="text-xl">SmartHunt</CardTitle>
          <CardDescription>{t("auth", "loginTagline")}</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} noValidate>
            <FieldGroup>
              <Field>
                <FieldLabel htmlFor="username">{t("auth", "username")}</FieldLabel>
                <Input
                  id="username"
                  autoComplete="username"
                  autoFocus
                  {...register("username")}
                />
                <FieldError errors={[errors.username]} />
              </Field>

              <Field>
                <FieldLabel htmlFor="password">{t("auth", "password")}</FieldLabel>
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
                {mutation.isPending ? t("auth", "loggingIn") : t("auth", "login")}
              </Button>

              <p className="text-center text-sm text-muted-foreground">
                {t("auth", "noAccountYet")}{" "}
                <Link href="/register" className="underline">
                  {t("auth", "createAccount")}
                </Link>
              </p>
            </FieldGroup>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
