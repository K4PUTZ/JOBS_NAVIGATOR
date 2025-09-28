cask 'sofa-jobs-navigator' do
  version :latest
  sha256 :no_check

  url 'https://example.com/Sofa Jobs Navigator.dmg'
  name 'Sofa Jobs Navigator'
  desc 'Desktop app for job navigation and task automation'
  homepage 'https://example.com'

  app 'Sofa Jobs Navigator.app'

  zap trash: [
    '~/Library/Application Support/sofa_jobs_navigator',
    '~/Library/Preferences/com.example.sofa-jobs-navigator.plist',
  ]
end
