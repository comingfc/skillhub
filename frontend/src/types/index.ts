export interface Skill {
  id: string
  namespace_id: string
  name: string
  slug: string
  version: string
  tags: string
  description: string | null
  readme: string | null
  download_count: number
  rating_avg: string
  rating_count: number
  status: string
  published_at: string | null
  created_at: string
  namespace_slug: string | null
  manifest?: Record<string, unknown>
  versions?: SkillVersion[]
}

export interface SkillVersion {
  id: string
  version: string
  changelog: string | null
  created_at: string
}

export interface Namespace {
  id: string
  name: string
  slug: string
  description: string | null
  visibility: string
  owner_id: string
  settings: Record<string, unknown>
  created_at: string
}

export interface NamespaceMember {
  id: string
  user_id: string
  role: string
  joined_at: string
  username: string
  email: string
}

export interface User {
  id: string
  email: string
  username: string
  avatar_url: string | null
  bio: string | null
  is_platform_admin: boolean
  created_at: string
}
