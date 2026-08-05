"use client";

import {
  BookOpen,
  CalendarClock,
  CircleHelp,
  Search,
  SearchCheck,
} from "lucide-react";
import { PageGlow } from "@/components/page-glow";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useTranslation } from "@/lib/i18n/language-context";

// This page's own long-form guide content (CardContent paragraphs below)
// is intentionally still Arabic-only in both languages — translating the
// deep prose here is a much larger, separate effort from the app-chrome
// translation (nav/titles/common actions) this pass covers. Only the
// section nav itself is bilingual.
const SECTIONS_AR = [
  { id: "overview", label: "نظرة عامة" },
  { id: "discovery", label: "اكتشاف الوظائف" },
  { id: "scoring", label: "نسبة التوافق" },
  { id: "resume", label: "السيرة الذاتية وخطاب التقديم" },
  { id: "apply", label: "التقديم التلقائي" },
  { id: "notifications", label: "الإشعارات" },
  { id: "faq", label: "أسئلة شائعة" },
];
const SECTIONS_EN = [
  { id: "overview", label: "Overview" },
  { id: "discovery", label: "Job Discovery" },
  { id: "scoring", label: "Match Score" },
  { id: "resume", label: "Resume & Cover Letter" },
  { id: "apply", label: "Auto-Apply" },
  { id: "notifications", label: "Notifications" },
  { id: "faq", label: "FAQ" },
];

export default function DocsPage() {
  const { t, locale } = useTranslation();
  const SECTIONS = locale === "ar" ? SECTIONS_AR : SECTIONS_EN;

  return (
    <div className="relative flex flex-col gap-6 overflow-hidden lg:flex-row lg:items-start">
      <PageGlow />
      <h1 className="sr-only">{t("pageTitles", "docs")}</h1>

      <nav className="top-6 flex shrink-0 flex-col gap-1 lg:sticky lg:w-48">
        <p className="mb-1 flex items-center gap-2 text-sm font-semibold text-muted-foreground">
          <BookOpen className="size-4" />
          {t("pageTitles", "docs")}
        </p>
        {SECTIONS.map((s) => (
          <a
            key={s.id}
            href={`#${s.id}`}
            className="rounded-md px-2 py-1.5 text-sm text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            {s.label}
          </a>
        ))}
      </nav>

      <div className="flex max-w-3xl flex-1 flex-col gap-8">
        <section id="overview" className="flex flex-col gap-3 scroll-mt-6">
          <h2 className="text-xl font-semibold">نظرة عامة</h2>
          <p className="text-sm leading-7 text-muted-foreground">
            SmartHunt نظام شخصي (لمستخدم واحد بس) بيدور على وظائف مناسبة
            لسيرتك الذاتية من مواقع التوظيف، بيقيّمها بالذكاء الاصطناعي،
            وبيجهزلك سيرة ذاتية وخطاب تقديم مخصصين لكل وظيفة. الهدف
            النهائي إن النظام يدور، يقيّم، ويقدّم لوحده بشكل كامل على
            جدول زمني — من غير ما تدوس &quot;تقديم&quot; بنفسك — وبعدين
            يبلغك إنه قدّم كام وظيفة النهارده. لحد دلوقتي التقديم
            التلقائي محتاج بيانات دخول حقيقية لمواقع التوظيف ولسه بيتم
            التأكد منه (شوف قسم &quot;التقديم التلقائي&quot; تحت).
          </p>
        </section>

        <section id="discovery" className="flex flex-col gap-4 scroll-mt-6">
          <h2 className="text-xl font-semibold">اكتشاف الوظائف</h2>
          <p className="text-sm leading-7 text-muted-foreground">
            فيه 3 طرق يجيبلك بيها المشروع وظائف، كلهم موجودين في تابة
            &quot;البحث عن وظائف&quot;:
          </p>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <CalendarClock className="size-4 text-teal-400" />
                البحث التلقائي المجدول
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm leading-7 text-muted-foreground">
              النظام بيبحث لوحده كل شوية ساعات على كلمات مفتاحية ثابتة
              (Linux, OpenShift, VMware, Storage) في السعودية بس، ويحفظ
              أي وظيفة جديدة تلاقيها في تابة &quot;الوظائف&quot;. زرار
              &quot;تشغيل بحث الآن&quot; في تابة البحث عن وظائف بيخليك
              تشغّل نفس البحث ده يدويًا بكلمة مفتاحية وموقع من اختيارك،
              بدل ما تستنى الجدولة.
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Search className="size-4 text-emerald-400" />
                البحث المباشر في موقع معيّن
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm leading-7 text-muted-foreground">
              في تابة &quot;الوظائف&quot;، لو اخترت اسم موقع معيّن (زي
              LinkedIn) بدل &quot;كل المواقع&quot; وعملت بحث، النظام
              هيروح يدور فعلاً في الموقع ده على طول (مش بس في الوظائف
              المحفوظة عندنا) ويحفظ اللي يلاقيه — ده بياخد وقت أطول
              شوية (نص دقيقة لدقيقة تقريبًا) لأنه بيفتح الموقع فعلاً.
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <SearchCheck className="size-4 text-sky-400" />
                البحث في بوستات لينكدان
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm leading-7 text-muted-foreground">
              بعض فرص العمل بتتنشر كبوست عادي على لينكدان مش كوظيفة
              رسمية. من نفس التابة تقدر تدوس &quot;افحص الصفحة الرئيسية
              بتاعتي&quot; (بيفحص أول 50 بوست في صفحتك الرئيسية) أو
              تضيف حسابات اتش آر بعينها وتفحصها يدويًا — أي بوست فيه
              فرصة عمل حقيقية بيتحفظلك كوظيفة عادية في تابة الوظائف
              (هتلاقي عليها علامة &quot;بوست&quot;).
            </CardContent>
          </Card>

          <p className="text-sm leading-7 text-muted-foreground">
            تقدر كمان تحفظ أي عملية بحث (كلمة مفتاحية + موقع) من تابة
            الوظائف بزرار &quot;احفظ البحث ده&quot;، وترجعلها تاني من
            تابة البحث عن وظائف بزرار &quot;أعد البحث&quot; من غير ما
            تكتب كل حاجة من الأول.
          </p>
        </section>

        <section id="scoring" className="flex flex-col gap-3 scroll-mt-6">
          <h2 className="text-xl font-semibold">نسبة التوافق</h2>
          <p className="text-sm leading-7 text-muted-foreground">
            نسبة التوافق اللي شايفها جنب كل وظيفة (0% لحد 100%) بتتحسب
            بمقارنة المهارات المذكورة في وصف الوظيفة بالمهارات المذكورة
            في سيرتك الذاتية المرفوعة — لازم يبقى عندك سيرة ذاتية مرفوعة
            من تابة &quot;السيرة الذاتية&quot; علشان الحساب ده يشتغل.
            وظيفة من غير أي مهارات معروفة في وصفها بتاخد 0% تلقائيًا —
            مش معناها إنها مش مناسبة، معناها إن الوصف نفسه مفيهوش تفاصيل
            كفاية.
          </p>
        </section>

        <section id="resume" className="flex flex-col gap-3 scroll-mt-6">
          <h2 className="text-xl font-semibold">السيرة الذاتية وخطاب التقديم</h2>
          <p className="text-sm leading-7 text-muted-foreground">
            من تابة &quot;السيرة الذاتية&quot; ترفع ملف PDF أو DOCX،
            والنظام بيستخرج النص منه ويستخدمه في كل حاجة تانية (البحث،
            التوافق، خطاب التقديم، المساعد الذكي). في نفس التابة تحت،
            تقدر تولّد خطاب تقديم مخصص لأي وظيفة عن طريق لصق وصفها —
            الذكاء الاصطناعي بيكتبلك خطاب حقيقي بناءً على سيرتك الذاتية
            الفعلية، وتقدر تراجعه وتعدله قبل ما تستخدمه. من صفحة أي
            وظيفة بالتحديد (لما تدوس عليها من تابة الوظائف) تقدر كمان
            تولّد نسخة من سيرتك الذاتية متخصصة لنفس الوظيفة دي.
          </p>
        </section>

        <section id="apply" className="flex flex-col gap-3 scroll-mt-6">
          <h2 className="text-xl font-semibold">التقديم التلقائي</h2>
          <p className="text-sm leading-7 text-muted-foreground">
            الهدف النهائي إن النظام يقدّم على الوظائف المناسبة لوحده
            (عن طريق متصفح حقيقي)، ويوقف بس لو قابل CAPTCHA، تحقق بخطوتين،
            أو سؤال في الطلب مش عارف يجاوب عليه — أي حاجة تانية المفروض
            تتم لوحدها من غير تدخل. ده شغال حاليًا مع مواقع بعينها بس
            (اللي فيها بيانات دخول محفوظة)، وأول ما يقدّم فعلاً هتوصلك
            رسالة تقولك عدد الوظائف اللي اتقدملها النهارده.
          </p>
        </section>

        <section id="notifications" className="flex flex-col gap-3 scroll-mt-6">
          <h2 className="text-xl font-semibold">الإشعارات</h2>
          <p className="text-sm leading-7 text-muted-foreground">
            من تابة &quot;الإعدادات&quot; تقدر تفعّل إشعارات تليجرام
            أو واتساب علشان توصلك رسالة أول ما حاجة مهمة تحصل (تقديم
            تلقائي نجح، رد على إيميل تقديم، إلخ) من غير ما تفضل فاتح
            المشروع طول الوقت.
          </p>
        </section>

        <section id="faq" className="flex flex-col gap-3 pb-8 scroll-mt-6">
          <h2 className="flex items-center gap-2 text-xl font-semibold">
            <CircleHelp className="size-5 text-slate-400" />
            أسئلة شائعة
          </h2>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">
                ليه بعض الوظائف مفيهاش تاريخ نشر؟
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">
              مش كل موقع بيدّي تاريخ نشر حقيقي — لو مش موجود، بنعرض
              تاريخ اكتشاف النظام للوظيفة بدل ما تفضل الخانة فاضية.
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">
                ليه المساعد الذكي أو توليد الخطابات بياخد وقت طويل؟
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">
              الذكاء الاصطناعي شغال محليًا على جهازك (مش عن طريق إنترنت)
              علشان مفيش تكلفة ولا خصوصية بياناتك بتتشارك — ده بياخد
              وقت أطول من خدمة سحابية، خصوصًا مع سيرة ذاتية طويلة. شريط
              التقدم بيفضل شغال طول ما الطلب لسه بيتنفذ.
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">
                فيه فرق بين المواقع المفعّلة في تابة &quot;مواقع
                التوظيف&quot;؟
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">
              أي موقع عليه علامة &quot;اكتشاف حقيقي&quot; بيدور فعلاً في
              الموقع الحقيقي. اللي عليه &quot;اكتشاف فقط (لسه مش
              حقيقي)&quot; لسه مبنيش بالكامل — مفيش داعي تفعّله دلوقتي.
            </CardContent>
          </Card>
        </section>
      </div>
    </div>
  );
}
