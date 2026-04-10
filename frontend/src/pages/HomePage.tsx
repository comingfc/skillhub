import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import api from '../api/client'
import SkillCard from '../components/SkillCard'
import { Skill } from '../types'

export default function HomePage() {
  const { data: skills, isLoading } = useQuery({
    queryKey: ['skills'],
    queryFn: async () => {
      const response = await api.get('/skills')
      return response.data as Skill[]
    },
  })

  return (
    <div>
      <section className="bg-primary-600 text-white py-16 rounded-2xl mb-8">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h1 className="text-4xl font-bold mb-4">
            Share Agent Skills with Your Team
          </h1>
          <p className="text-xl text-primary-100 mb-8">
            A self-hosted platform for teams to discover, share, and govern agent skills privately.
          </p>
          <div className="flex justify-center gap-4">
            <Link
              to="/explore"
              className="bg-white text-primary-600 px-6 py-3 rounded-lg font-medium hover:bg-primary-50"
            >
              Explore Skills
            </Link>
            <Link
              to="/register"
              className="bg-primary-700 text-white px-6 py-3 rounded-lg font-medium hover:bg-primary-800"
            >
              Get Started
            </Link>
          </div>
        </div>
      </section>

      <section>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Featured Skills</h2>
          <Link to="/explore" className="text-primary-600 hover:text-primary-700">
            View all
          </Link>
        </div>

        {isLoading ? (
          <div className="text-center py-12">Loading...</div>
        ) : skills?.length ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {skills.slice(0, 6).map((skill) => (
              <SkillCard key={skill.id} skill={skill} />
            ))}
          </div>
        ) : (
          <div className="text-center py-12 text-gray-500">
            <p>No skills published yet.</p>
            <Link to="/upload" className="text-primary-600 hover:text-primary-700 mt-2 inline-block">
              Upload the first skill
            </Link>
          </div>
        )}
      </section>
    </div>
  )
}
