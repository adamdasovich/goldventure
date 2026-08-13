"""
Core models package.

All models are re-exported here so that `from core.models import ModelName`
continues to work everywhere.
"""

from .users import (  # noqa: F401
    User,
    Company,
)
from .mining import (  # noqa: F401
    Project,
    ResourceEstimate,
    EconomicStudy,
    Financing,
    Investor,
    InvestorPosition,
)
from .market import (  # noqa: F401
    MarketData,
    CommodityPrice,
    MetalPrice,
    StockPrice,
)
from .news import (  # noqa: F401
    NewsRelease,
    Document,
    DocumentChunk,
    NewsChunk,
    DocumentProcessingJob,
    NewsSource,
    NewsArticle,
    NewsScrapeJob,
    NewsReleaseFlag,
    NewsReportFlag,
    DismissedNewsURL,
    CompanyPerson,
    CompanyDocument,
    CompanyNews,
    ScrapingJob,
    FailedCompanyDiscovery,
    CompanyVerificationLog,
    FailedTaskLog,
)
from .community import (  # noqa: F401
    InvestorCommunication,
    CompanyMetrics,
    Watchlist,
    Alert,
    ForumDiscussion,
    ForumMessage,
    GuestSpeakerSession,
    SessionSpeaker,
    SessionModerator,
    SessionQuestion,
    QuestionUpvote,
    UserPresence,
    SessionNotification,
    SessionParticipant,
    SpeakerEvent,
    EventSpeaker,
    EventRegistration,
    EventQuestion,
    EventReaction,
    GlossaryTerm,
    GlossaryTermSubmission,
    UserAIUsage,
    PlatformSubscription,
    PlatformSubscriptionInvoice,
    ProcessedStripeEvent,
)
from .properties import (  # noqa: F401
    ProspectorProfile,
    ProspectorCommissionAgreement,
    PropertyListing,
    PropertyMedia,
    PropertyInquiry,
    InquiryMessage,
    PropertyWatchlist,
    SavedPropertySearch,
    FeaturedPropertyConfig,
    CompanyResource,
    SpeakingEvent,
    CompanySubscription,
    SubscriptionInvoice,
    CompanyAccessRequest,
)
from .financial_hub import (  # noqa: F401
    EducationalModule,
    ModuleCompletion,
    AccreditedInvestorQualification,
    SubscriptionAgreement,
    InvestmentTransaction,
    FinancingAggregate,
    PaymentInstruction,
    DRSDocument,
    InvestmentInterest,
    InvestmentInterestAggregate,
)
from .reports import (  # noqa: F401
    WeeklyIndustryReport,
)
from .store import (  # noqa: F401
    StoreCategory,
    StoreProduct,
    StoreProductImage,
    StoreProductVariant,
    StoreDigitalAsset,
    StoreCart,
    StoreCartItem,
    StoreOrder,
    StoreOrderItem,
    StoreShippingRate,
    StoreProductShare,
    StoreRecentPurchase,
    StoreProductInquiry,
    UserStoreBadge,
)
