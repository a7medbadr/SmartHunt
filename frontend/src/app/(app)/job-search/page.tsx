"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Rss, SearchCheck, Trash2 } from "lucide-react";
import { useState } from "react";

import { searchProvider } from "@/lib/scheduler-api";
import { listProviders } from "@/lib/providers-api";
import { PageGlow } from "@/components/page-glow";
import {
  addHashtag,
  addMonitoredAccount,
  listHashtags,
  listMonitoredAccounts,
  removeHashtag,
  removeMonitoredAccount,
  scanAccountNow,
  scanHashtagNow,
  scanHomeFeedNow,
  setHashtagEnabled,
  setMonitoredAccountEnabled,
} from "@/lib/linkedin-monitor-api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useTranslation } from "@/lib/i18n/language-context";
import { Switch } from "@/components/ui/switch";

export default function JobSearchPage() {
  const queryClient = useQueryClient();
  const { t } = useTranslation();

  // 1) افحص الصفحة الرئيسية بتاعتي — منفصل خالص عن بلوك البحث في بوستات
  // لينكدان بتاع الحسابات، بلوك لوحده زي ما اتطلب.
  const [scanResultMessage, setScanResultMessage] = useState<string | null>(null);

  const scanFeedMutation = useMutation({
    mutationFn: scanHomeFeedNow,
    onSuccess: (result) => {
      setScanResultMessage(`لقينا ${result.scanned} بوست، وحفظنا ${result.saved} وظيفة مناسبة.`);
      queryClient.invalidateQueries({ queryKey: ["search-jobs"] });
    },
    onError: () => setScanResultMessage("حصل خطأ أثناء الفحص، جرب تاني."),
  });

  // 2) البحث في بوستات لينكدان — حسابات الأشخاص/الاتش آر.
  const [newAccountUrl, setNewAccountUrl] = useState("");
  const [newAccountLabel, setNewAccountLabel] = useState("");
  const [accountScanMessage, setAccountScanMessage] = useState<string | null>(null);

  const accountsQuery = useQuery({
    queryKey: ["linkedin-monitor-accounts"],
    queryFn: listMonitoredAccounts,
  });

  // A single shared Playwright page (browser_manager.get_page("linkedin"))
  // backs every account scan — two scans in flight at once would race on
  // the same page's navigation. queuedAccountIds serializes them: adding
  // 3 accounts back-to-back (each auto-scanning itself) or clicking
  // several rows quickly no longer fires overlapping requests, each
  // waits its turn instead.
  const [scanQueue, setScanQueue] = useState<number[]>([]);

  const scanAccountMutation = useMutation({
    mutationFn: scanAccountNow,
    onSuccess: (result) => {
      setAccountScanMessage(
        `لقينا ${result.scanned} بوست، وحفظنا ${result.saved} وظيفة مناسبة.`,
      );
      queryClient.invalidateQueries({ queryKey: ["linkedin-monitor-accounts"] });
      queryClient.invalidateQueries({ queryKey: ["search-jobs"] });
    },
    onError: () => setAccountScanMessage("حصل خطأ أثناء الفحص، جرب تاني."),
    onSettled: () => {
      setScanQueue((queue) => {
        const [next, ...rest] = queue;
        if (next !== undefined) scanAccountMutation.mutate(next);
        return rest;
      });
    },
  });

  function queueAccountScan(accountId: number) {
    if (!scanAccountMutation.isPending) {
      scanAccountMutation.mutate(accountId);
    } else {
      setScanQueue((queue) => (queue.includes(accountId) ? queue : [...queue, accountId]));
    }
  }

  const addAccountMutation = useMutation({
    mutationFn: addMonitoredAccount,
    onSuccess: (account) => {
      setNewAccountUrl("");
      setNewAccountLabel("");
      queryClient.invalidateQueries({ queryKey: ["linkedin-monitor-accounts"] });
      // "أضف حساب" مش بس بيحفظ الرابط — لازم كمان يدور على طول في بوستات
      // الحساب ده عن وظائف مرتبطة بيا، مش يسيبه لحد ما أدوس "افحص دلوقتي"
      // بنفسي بعدين.
      queueAccountScan(account.id);
    },
  });

  const toggleAccountMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: number; enabled: boolean }) =>
      setMonitoredAccountEnabled(id, enabled),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["linkedin-monitor-accounts"] }),
  });

  const removeAccountMutation = useMutation({
    mutationFn: removeMonitoredAccount,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["linkedin-monitor-accounts"] }),
  });

  // 3) بحث في مواقع التوظيف — بحث يدوي مباشر في موقع معيّن (غير الأوتوماتيك).
  const [siteKeyword, setSiteKeyword] = useState("");
  const [siteName, setSiteName] = useState("");
  const [siteSearchError, setSiteSearchError] = useState<string | null>(null);

  const providersQuery = useQuery({
    queryKey: ["providers"],
    queryFn: listProviders,
  });
  const enabledProviders = providersQuery.data?.filter((p) => p.enabled) ?? [];

  const siteSearchMutation = useMutation({
    mutationFn: () => searchProvider(siteName, siteKeyword),
  });

  function handleSiteSearch() {
    setSiteSearchError(null);
    if (!siteKeyword.trim() || !siteName) {
      setSiteSearchError("محتاج كلمة مفتاحية واسم موقع علشان يبحث.");
      return;
    }
    siteSearchMutation.mutate(undefined, {
      onSuccess: () => queryClient.invalidateQueries({ queryKey: ["search-jobs"] }),
    });
  }

  // 4) البحث بالهاشتاج — نفس فكرة بلوك حسابات لينكدان بالظبط: كل هاشتاج
  // صف لوحده، بزرار تفعيل/تعطيل وزرار "افحص دلوقتي" وزرار حذف، بدل مربع
  // نص واحد أو أزرار متفرقة. نفس فكرة الطابور بتاعة queueAccountScan فوق
  // — علشان لو ضغط على أكتر من هاشتاج ورا بعض، كل فحص يستنى دوره بدل ما
  // يتزاحموا على نفس صفحة لينكدان.
  const [newHashtagTag, setNewHashtagTag] = useState("");
  const [hashtagScanMessage, setHashtagScanMessage] = useState<string | null>(null);
  const [hashtagScanQueue, setHashtagScanQueue] = useState<number[]>([]);

  const hashtagsQuery = useQuery({
    queryKey: ["linkedin-hashtags"],
    queryFn: listHashtags,
  });

  const hashtagScanMutation = useMutation({
    mutationFn: scanHashtagNow,
    onSuccess: (result) => {
      setHashtagScanMessage(`لقينا ${result.scanned} بوست، وحفظنا ${result.saved} وظيفة مناسبة.`);
      queryClient.invalidateQueries({ queryKey: ["linkedin-hashtags"] });
      queryClient.invalidateQueries({ queryKey: ["search-jobs"] });
    },
    onError: () => setHashtagScanMessage("حصل خطأ أثناء الفحص، جرب تاني."),
    onSettled: () => {
      setHashtagScanQueue((queue) => {
        const [next, ...rest] = queue;
        if (next !== undefined) hashtagScanMutation.mutate(next);
        return rest;
      });
    },
  });

  function queueHashtagScan(hashtagId: number) {
    if (!hashtagScanMutation.isPending) {
      hashtagScanMutation.mutate(hashtagId);
    } else {
      setHashtagScanQueue((queue) =>
        queue.includes(hashtagId) ? queue : [...queue, hashtagId],
      );
    }
  }

  const addHashtagMutation = useMutation({
    mutationFn: addHashtag,
    onSuccess: (hashtag) => {
      setNewHashtagTag("");
      queryClient.invalidateQueries({ queryKey: ["linkedin-hashtags"] });
      // زي "أضف حساب" بالظبط — أول ما يتضاف الهاشتاج، يتفحص على طول.
      queueHashtagScan(hashtag.id);
    },
  });

  const toggleHashtagMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: number; enabled: boolean }) =>
      setHashtagEnabled(id, enabled),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["linkedin-hashtags"] }),
  });

  const removeHashtagMutation = useMutation({
    mutationFn: removeHashtag,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["linkedin-hashtags"] }),
  });


  return (
    <div className="relative flex flex-col gap-6 overflow-hidden">
      <PageGlow />
      <h1 className="flex items-center gap-2 text-2xl font-semibold">
        <SearchCheck className="size-6 text-teal-400" />
        {t("pageTitles", "jobSearch")}
      </h1>

      {/* 1) افحص الصفحة الرئيسية بتاعتي — بلوك لوحده، أول حاجة فوق */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Rss className="size-4 text-sky-400" />
            افحص الصفحة الرئيسية بتاعتي
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <p className="text-sm text-muted-foreground">
            بيدور في أول 50 بوست في صفحتك الرئيسية على لينكدان (مش بس
            الحسابات اللي متابعها) — أي بوست فيه فرصة عمل حقيقية مرتبطة
            بشغلك بيتحفظ تلقائيًا في تابة الوظائف بعلامة &quot;بوست&quot;.
            النظام كمان بيعمل الفحص ده لوحده كل ساعة من غير ما تحتاج تدوس
            حاجة.
          </p>
          <Button
            variant="secondary"
            disabled={scanFeedMutation.isPending}
            onClick={() => scanFeedMutation.mutate()}
            className="self-start"
          >
            {scanFeedMutation.isPending
              ? "جاري فحص الصفحة الرئيسية..."
              : "افحص الصفحة الرئيسية بتاعتي"}
          </Button>
          {scanResultMessage && <p className="text-sm text-primary">{scanResultMessage}</p>}
        </CardContent>
      </Card>

      {/* 2) البحث في بوستات لينكدان — حسابات الأشخاص/الاتش آر */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Rss className="size-4 text-sky-400" />
            البحث في بوستات لينكدان
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <p className="text-sm text-muted-foreground">
            بعض فرص العمل بتتنشر كبوست عادي على لينكدان مش كوظيفة رسمية —
            سواء من حساب اتش آر بعينه، أو أي حد بيشير بوست وظيفة. ضيف هنا
            رابط بروفايل الشخص، وهيتفحص على طول ويدور على وظائف مرتبطة
            بيك في بوستاته — وبعد كده النظام بيعمله فحص يومي لوحده لآخر
            24 ساعة.
          </p>

          <div className="flex flex-wrap gap-2">
            <Input
              placeholder="رابط بروفايل لينكدان (https://linkedin.com/in/...)"
              value={newAccountUrl}
              onChange={(e) => setNewAccountUrl(e.target.value)}
              className="max-w-sm"
            />
            <Input
              placeholder="اسم/ملاحظة (اختياري)"
              value={newAccountLabel}
              onChange={(e) => setNewAccountLabel(e.target.value)}
              className="max-w-xs"
            />
            <Button
              disabled={!newAccountUrl.trim() || addAccountMutation.isPending}
              onClick={() =>
                addAccountMutation.mutate({
                  profileUrl: newAccountUrl.trim(),
                  label: newAccountLabel.trim(),
                })
              }
            >
              {addAccountMutation.isPending ? "جاري الإضافة والفحص..." : "أضف حساب"}
            </Button>
          </div>

          {accountsQuery.isPending ? (
            <Skeleton className="h-20 w-full" />
          ) : accountsQuery.data && accountsQuery.data.length > 0 ? (
            <div className="flex flex-col gap-2">
              {accountsQuery.data.map((account) => (
                <div
                  key={account.id}
                  className="flex flex-wrap items-center justify-between gap-2 rounded-md border p-3"
                >
                  <div className="flex flex-col">
                    <a
                      href={account.profile_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm underline"
                    >
                      {account.label || account.profile_url}
                    </a>
                    <span className="text-xs text-muted-foreground">
                      {account.last_checked_at
                        ? `آخر فحص: ${new Date(account.last_checked_at).toLocaleString("ar-SA")}`
                        : "لسه ماتفحصش"}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Switch
                      checked={account.enabled}
                      onCheckedChange={(checked) =>
                        toggleAccountMutation.mutate({ id: account.id, enabled: checked })
                      }
                      disabled={toggleAccountMutation.isPending}
                    />
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => queueAccountScan(account.id)}
                    >
                      {scanAccountMutation.isPending &&
                      scanAccountMutation.variables === account.id
                        ? "جاري الفحص..."
                        : scanQueue.includes(account.id)
                          ? "في الانتظار..."
                          : "افحص دلوقتي"}
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => removeAccountMutation.mutate(account.id)}
                    >
                      <Trash2 className="size-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">لسه مفيش حسابات متابَعة.</p>
          )}

          {accountScanMessage && <p className="text-sm text-primary">{accountScanMessage}</p>}
        </CardContent>
      </Card>

      {/* 3) بحث في مواقع التوظيف — بحث يدوي في موقع معيّن */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">بحث في مواقع التوظيف</CardTitle>
          <p className="text-xs text-muted-foreground">
            بحث يدوي مباشر في موقع معيّن — غير البحث التلقائي اللي المشروع
            بيعمله لوحده كل يوم الصبح.
          </p>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <div className="flex flex-wrap gap-2">
            <Input
              placeholder="كلمة مفتاحية"
              value={siteKeyword}
              onChange={(e) => setSiteKeyword(e.target.value)}
              className="max-w-xs"
            />
            <Select value={siteName} onValueChange={(value) => setSiteName(value ?? "")}>
              <SelectTrigger className="w-44">
                <SelectValue placeholder="اختار الموقع" />
              </SelectTrigger>
              <SelectContent>
                {enabledProviders.map((p) => (
                  <SelectItem key={p.name} value={p.name} className="capitalize">
                    {p.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button onClick={handleSiteSearch} disabled={siteSearchMutation.isPending}>
              {siteSearchMutation.isPending ? "جاري البحث..." : "بحث"}
            </Button>
          </div>

          {siteSearchError && <p className="text-sm text-destructive">{siteSearchError}</p>}
          {siteSearchMutation.isError && !siteSearchError && (
            <p className="text-sm text-destructive">حصل خطأ أثناء البحث، جرب تاني.</p>
          )}
          {siteSearchMutation.data && (
            <p className="text-sm text-primary">
              لقينا {siteSearchMutation.data.found} وظيفة في {siteSearchMutation.data.provider}،
              {" "}أضفنا {siteSearchMutation.data.inserted} جديدة (
              {siteSearchMutation.data.duplicates} كانت موجودة قبل كده).
            </p>
          )}
        </CardContent>
      </Card>

      {/* 4) البحث بالهاشتاج — نفس بلوك حسابات لينكدان بالظبط: صف لكل هاشتاج */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">البحث بالهاشتاج</CardTitle>
          <p className="text-xs text-muted-foreground">
            كل هاشتاج بيفحص أول 50 بوست فيه ويحفظ أي وظيفة مناسبة تلقائيًا.
            النظام كمان بيعمل فحص لكل الهاشتاجات المفعّلة دي مرة كل يوم
            لوحده من غير ما تحتاج تدوس حاجة.
          </p>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div className="flex flex-wrap gap-2">
            <Input
              placeholder="اسم الهاشتاج (من غير #)"
              value={newHashtagTag}
              onChange={(e) => setNewHashtagTag(e.target.value)}
              className="max-w-xs"
            />
            <Button
              disabled={!newHashtagTag.trim() || addHashtagMutation.isPending}
              onClick={() => addHashtagMutation.mutate(newHashtagTag.trim())}
            >
              {addHashtagMutation.isPending ? "جاري الإضافة والفحص..." : "أضف هاشتاج"}
            </Button>
          </div>

          {hashtagsQuery.isPending ? (
            <Skeleton className="h-20 w-full" />
          ) : hashtagsQuery.data && hashtagsQuery.data.length > 0 ? (
            <div className="flex flex-col gap-2">
              {hashtagsQuery.data.map((hashtag) => (
                <div
                  key={hashtag.id}
                  className="flex flex-wrap items-center justify-between gap-2 rounded-md border p-3"
                >
                  <div className="flex flex-col">
                    <span className="text-sm">#{hashtag.tag}</span>
                    <span className="text-xs text-muted-foreground">
                      {hashtag.last_checked_at
                        ? `آخر فحص: ${new Date(hashtag.last_checked_at).toLocaleString("ar-SA")}`
                        : "لسه ماتفحصش"}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Switch
                      checked={hashtag.enabled}
                      onCheckedChange={(checked) =>
                        toggleHashtagMutation.mutate({ id: hashtag.id, enabled: checked })
                      }
                      disabled={toggleHashtagMutation.isPending}
                    />
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => queueHashtagScan(hashtag.id)}
                    >
                      {hashtagScanMutation.isPending &&
                      hashtagScanMutation.variables === hashtag.id
                        ? "جاري الفحص..."
                        : hashtagScanQueue.includes(hashtag.id)
                          ? "في الانتظار..."
                          : "افحص دلوقتي"}
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => removeHashtagMutation.mutate(hashtag.id)}
                    >
                      <Trash2 className="size-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">لسه مفيش هاشتاجات.</p>
          )}
          {hashtagScanMessage && <p className="text-sm text-primary">{hashtagScanMessage}</p>}
        </CardContent>
      </Card>
    </div>
  );
}
