import type { FC } from 'react'
import {
  useEffect,
  useState,
  useRef
} from 'react'
import { useAsyncEffect } from 'ahooks'
import {
  ChatWithHistoryContext,
  useChatWithHistoryContext,
} from './context'
import { useChatWithHistory } from './hooks'
import Sidebar from './sidebar'
import HeaderInMobile from './header-in-mobile'
import ConfigPanel from './config-panel'
import ChatWrapper from './chat-wrapper'
import type { InstalledApp } from '@/models/explore'
import Loading from '@/app/components/base/loading'
import useBreakpoints, { MediaType } from '@/hooks/use-breakpoints'
import { checkOrSetAccessToken } from '@/app/components/share/utils'
import AppUnavailable from '@/app/components/base/app-unavailable'
import { PostHogProvider, usePostHog } from 'posthog-js/react'

const useQuery = () => {
  return new URLSearchParams(window.location.search);
}

type ChatWithHistoryProps = {
  className?: string
}
const ChatWithHistory: FC<ChatWithHistoryProps> = ({
  className,
}) => {
  const {
    appInfoError,
    appData,
    appInfoLoading,
    appPrevChatList,
    showConfigPanelBeforeChat,
    appChatListDataLoading,
    chatShouldReloadKey,
    isMobile,
  } = useChatWithHistoryContext()

  const hasPosthogUserBeenIdentified = useRef<boolean>(false)
  const query = useQuery()
  const posthog = usePostHog()
  const chatReady = (!showConfigPanelBeforeChat || !!appPrevChatList.length)
  const customConfig = appData?.custom_config
  const site = appData?.site

  useEffect(() => {
    if (site) {
      if (customConfig)
        document.title = `${site.title}`
      else
        document.title = `${site.title} - Powered by Dify`
    }
  }, [site, customConfig])

  useEffect(() => {
    if(!hasPosthogUserBeenIdentified.current){
      const username = query.get('username')
      if(username){
        posthog.identify(username)
        hasPosthogUserBeenIdentified.current = true
      }
    }
  }, [])

  if (appInfoLoading) {
    return (
      <Loading type='app' />
    )
  }

  if (appInfoError) {
    return (
      <AppUnavailable />
    )
  }

  return (
      <div className={`h-full flex bg-white ${className} ${isMobile && 'flex-col'}`}>
        {
          !isMobile && (
            <Sidebar />
          )
        }
        {
          isMobile && (
            <HeaderInMobile />
          )
        }
        <div className={`grow overflow-hidden ${showConfigPanelBeforeChat && !appPrevChatList.length && 'flex items-center justify-center'}`}>
          {
            showConfigPanelBeforeChat && !appChatListDataLoading && !appPrevChatList.length && (
              <div className={`flex w-full items-center justify-center h-full ${isMobile && 'px-4'}`}>
                <ConfigPanel />
              </div>
            )
          }
          {
            appChatListDataLoading && chatReady && (
              <Loading type='app' />
            )
          }
          {
            chatReady && !appChatListDataLoading && (
              <ChatWrapper key={chatShouldReloadKey} username={query.get('username')} />
            )
          }
        </div>
      </div>
  )
}

export type ChatWithHistoryWrapProps = {
  installedAppInfo?: InstalledApp
  className?: string
}
const ChatWithHistoryWrap: FC<ChatWithHistoryWrapProps> = ({
  installedAppInfo,
  className,
}) => {
  const media = useBreakpoints()
  const isMobile = media === MediaType.mobile

  const {
    appInfoError,
    appInfoLoading,
    appData,
    appParams,
    appMeta,
    appChatListDataLoading,
    currentConversationId,
    currentConversationItem,
    appPrevChatList,
    pinnedConversationList,
    conversationList,
    showConfigPanelBeforeChat,
    newConversationInputs,
    handleNewConversationInputsChange,
    inputsForms,
    handleNewConversation,
    handleStartChat,
    handleChangeConversation,
    handlePinConversation,
    handleUnpinConversation,
    handleDeleteConversation,
    conversationRenaming,
    handleRenameConversation,
    handleConversationCompleted,
    handleNewConversationStarted,
    chatShouldReloadKey,
    isInstalledApp,
    appId,
    handleFeedback,
    currentChatInstanceRef,
    conversationChatList, 
    setConversationChatList,
    handleConversationMessageSend
  } = useChatWithHistory(installedAppInfo)

  return (
    <ChatWithHistoryContext.Provider value={{
      appInfoError,
      appInfoLoading,
      appData,
      appParams,
      appMeta,
      appChatListDataLoading,
      currentConversationId,
      currentConversationItem,
      appPrevChatList,
      pinnedConversationList,
      conversationList,
      showConfigPanelBeforeChat,
      newConversationInputs,
      handleNewConversationInputsChange,
      inputsForms,
      handleNewConversation,
      handleStartChat,
      handleChangeConversation,
      handlePinConversation,
      handleUnpinConversation,
      handleDeleteConversation,
      conversationRenaming,
      handleRenameConversation,
      handleConversationCompleted,
      handleNewConversationStarted,
      chatShouldReloadKey,
      isMobile,
      isInstalledApp,
      appId,
      handleFeedback,
      currentChatInstanceRef,
      conversationChatList, 
      setConversationChatList,
      handleConversationMessageSend
    }}>
      <PostHogProvider apiKey="phc_XoOaVreBJqQa76OR3ocRu4FhRd0AMa8E6lgdCrXmpSs">
        <ChatWithHistory className={className} />
      </PostHogProvider>
    </ChatWithHistoryContext.Provider>
  )
}

const ChatWithHistoryWrapWithCheckToken: FC<ChatWithHistoryWrapProps> = ({
  installedAppInfo,
  className,
}) => {
  const [inited, setInited] = useState(false)
  const [appUnavailable, setAppUnavailable] = useState<boolean>(false)
  const [isUnknwonReason, setIsUnknwonReason] = useState<boolean>(false)

  useAsyncEffect(async () => {
    if (!inited) {
      if (!installedAppInfo) {
        try {
          await checkOrSetAccessToken()
        }
        catch (e: any) {
          if (e.status === 404) {
            setAppUnavailable(true)
          }
          else {
            setIsUnknwonReason(true)
            setAppUnavailable(true)
          }
        }
      }
      setInited(true)
    }
  }, [])

  if (appUnavailable)
    return <AppUnavailable isUnknwonReason={isUnknwonReason} />

  if (!inited)
    return null

  return (
    <ChatWithHistoryWrap
      installedAppInfo={installedAppInfo}
      className={className}
    />
  )
}

export default ChatWithHistoryWrapWithCheckToken
