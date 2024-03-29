<template>
  <div class="tokens">
    <top-bar title="Tokens"></top-bar>
    <v-container>
      <v-row v-if="activeUser">
        <v-col cols="12" class="text-center">
          <h1>You are looking at {{activeUser.fullname}}s tokens</h1>
        </v-col>
      </v-row>
      <v-row v-if="localState.createdToken">
        <v-col cols="12" md="10" offset-md="1">
          <v-alert prominent type="info" border="left" dismissible>
            <div class="text-h5">
              Here is your new token!
            </div>
            <div>
              <code class="generatedToken">{{localState.createdToken.generatedToken}}
                <v-btn icon small @click="copyToken(localState.createdToken)"><v-icon>mdi-content-copy</v-icon></v-btn>
              </code>
            </div>
            <div>
              Please commit it to memory or entrust it to your favorite password manager. You will never see it again!
            </div>
          </v-alert>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="12" md="10" offset-md="1">
          <v-data-table
            id="tokens"
            :headers="headers"
            :items="tokens"
            :search="localState.search"
            :sort-by="localState.sortBy"
            :sort-desc="localState.sortDesc"
            :loading="loading">
            <template v-slot:top>
              <v-toolbar flat>
                <v-text-field 
                  v-model="localState.search" 
                  prepend-inner-icon="mdi-magnify" 
                  label="Search..." 
                  single-line outlined dense hide-details></v-text-field>
                <v-spacer></v-spacer>
                <v-dialog v-model="localState.showEdit" max-width="500px">
                  <template v-slot:activator="{ on, attrs }">
                    <v-btn 
                      dense depressed
                      v-bind="attrs" v-on="on">Create Token</v-btn>
                  </template>
                  <v-card>
                    <v-card-title class="headline">{{editTitle}}</v-card-title>
                    <v-card-text>
                      <v-container>
                        <v-row>
                          <v-col cols="12">
                            <v-text-field v-model="localState.editItem.comment" label="Comment"></v-text-field>
                          </v-col>
                        </v-row>
                        <v-row>
                          <v-col cols="12">
                            <v-menu v-model="localState.showExpiration"
                              :close-on-content-click="false"
                              offset-y min-width="200px">
                              <template v-slot:activator="{ on, attrs }">
                                <v-text-field v-model="editExpiration" 
                                  prepend-icon="mdi-calendar"
                                  readonly
                                  v-bind="attrs"
                                  v-on="on"
                                  label="Expiration"></v-text-field>
                              </template> 
                              <v-date-picker v-model="editExpiration" @input="localState.showExpiration=false">
                              </v-date-picker>
                            </v-menu>
                          </v-col>
                        </v-row>
                      </v-container>
                    </v-card-text>
                    <v-card-actions>
                      <v-spacer></v-spacer>
                      <v-btn color="warning accent-1" text @click="closeEdit">Maybe not today.</v-btn>
                      <v-btn color="primary darken-1" text @click="save">Save it!</v-btn>
                    </v-card-actions>
                  </v-card>
                </v-dialog>
                <v-dialog v-model="localState.showDelete" max-width="500px">
                  <v-card>
                    <v-card-title class="headline">You really want to kick it?</v-card-title>
                    <v-card-actions>
                      <v-spacer></v-spacer>
                      <v-btn color="primary darken-1" text @click="closeDelete">Give it another chance.</v-btn>
                      <v-btn color="warning accent-1" text @click="deleteTokenConfirm">Get it out of my eyes.</v-btn>
                    </v-card-actions>
                  </v-card>
                </v-dialog>
                <v-btn 
                  id="refresh" 
                  class="ml-2"
                  dense depressed 
                  @click="loadTokens()"><v-icon>mdi-refresh</v-icon></v-btn>
              </v-toolbar>
            </template>
            <!-- eslint-disable-next-line vue/valid-v-slot -->
            <template v-slot:item.token="{ item }">
              <code>{{item.key_uid }}</code>
            </template>
            <!-- eslint-disable-next-line vue/valid-v-slot -->
            <template v-slot:item.expiresAt="{ item }">
              <span v-if="item.expiresAt">
                {{item.expiresAt | prettyDateTime}}
              </span>
              <span v-else>
                <em>no expiration</em>
              </span>
            </template>
            <!-- eslint-disable-next-line vue/valid-v-slot -->
            <template v-slot:item.actions="{ item }">
              <v-icon
                small
                class="mr-2"
                @click="editToken(item)">
                mdi-pencil
              </v-icon>
              <v-icon
                small
                @click="deleteToken(item)">
                mdi-delete
              </v-icon>
            </template>
          </v-data-table>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>
<style scoped>
code.generatedToken {
  font-size: 1.1rem;
  background-color: #cfe4f5;
  color: #111;
}
code.generatedToken .v-icon {
  color: #111;
}
</style>

<script lang="ts">
import Vue from 'vue';
import { Token, User } from '../store/models';
import { clone as _clone } from 'lodash';
import moment from 'moment';
import { DataTableHeader } from 'vuetify';

interface State {
  search: string;
  sortBy: string;
  sortDesc: boolean;
  showEdit: boolean;
  showDelete: boolean;
  showExpiration: boolean;
  editItem: Token;
  createdToken: Token | null;
}

export default Vue.extend({
  name: 'HskTokens',
  mounted() {
    this.localState.createdToken = null;
    this.loadTokens();
  },
  watch: {
    $route() {
      this.loadTokens();
    },
    'localState.showEdit': function showEdit(val) {
      if (!val) {
        this.closeEdit();
      }
    },
    'localState.showDelete': function showDelete(val) {
      if (!val) {
        this.closeDelete();
      }
    },
  },
  data: (): { headers: DataTableHeader[]; localState: State } => ({
    headers: [
      { text: 'id', value: 'id', sortable: true, filterable: false, width: '9%' },
      { text: 'Key ID', value: 'token', sortable: false, width: '20%' },
      { text: 'Comment', value: 'comment', sortable: true, width: '' },
      { text: 'Expires', value: 'expiresAt', sortable: true, filterable: false, width: '20%' },
      { text: 'Actions', value: 'actions', sortable: false, filterable: false, width: '1%' },
    ],
    localState: {
      search: '',
      showEdit: false,
      showDelete: false,
      showExpiration: false,
      editItem: new Token(),
      sortBy: 'id',
      sortDesc: false,
      createdToken: null,
    },
  }),
  computed: {
    tokens(): Token[] {
      return this.$store.getters['tokens/tokens'];
    },
    loading(): boolean {
      return this.$store.getters['tokens/status']==='loading';
    },
    editTitle(): string {
      return this.localState.editItem.id ? 'Edit Token' : 'New Token';
    },
    activeUser(): User | null {
      return this.$route.params.user ? this.$store.getters['tokens/user'] : null;
    },
    editExpiration: {
      get: function(): string {
        return this.localState.editItem.expiresAt ? 
          moment(this.localState.editItem.expiresAt).format('YYYY-MM-DD') :
          "";
      },
      set: function(val: string) {
        this.localState.editItem.expiresAt = new Date(val);
      }
    }
  },
  methods: {
    loadTokens() {
      if (this.$route.params.user) {
        this.$store.dispatch('users/get', this.$route.params.user)
          .then(user => {
            this.$store.commit('tokens/setActiveUser', user);
            this.$store.dispatch('tokens/list')
              .catch(err => this.$store.commit('snackbar/showError', err));
          })
          .catch(err => this.$store.commit('snackbar/showError', err));
      }
      else {
        this.$store.commit('tokens/setActiveUser', null);
        this.$store.dispatch('tokens/list')
          .catch(err => this.$store.commit('snackbar/showError', err));
      }
    },
    editToken(token: Token) {
      this.localState.editItem = _clone(token);
      this.localState.showEdit = true;
    },
    deleteToken(token: Token) {
      this.localState.editItem = _clone(token);
      this.localState.showDelete = true;
    },
    deleteTokenConfirm() {
       this.$store.dispatch('tokens/delete', this.localState.editItem.id)
        .then(() => this.$store.commit('snackbar/showSuccess', 'Gone!'))
        .catch(err => this.$store.commit('snackbar/showError', err))
       this.closeDelete();
    },
    closeEdit() {
      this.localState.showEdit = false;
      this.$nextTick(() => {
        this.localState.editItem = new Token();
      });
    },
    closeDelete() {
      this.localState.showDelete = false;
      this.$nextTick(() => {
        this.localState.editItem = new Token();
      });
    },
    save() {
      const action = this.localState.editItem.id ?
        'tokens/update' : 'tokens/create';
      this.$store.dispatch(action, this.localState.editItem)
        .then(upd => {
          this.$store.commit('snackbar/showSuccess', 'Saved!');
          if (action === 'tokens/create') {
            this.localState.createdToken = upd;
          }
        })
        .catch(err => this.$store.commit('snackbar/showError', err))
      this.closeEdit();
    },
    copyToken(item: Token) {
      this.$copyText(item.generatedToken)
        .then(() => this.$store.commit('snackbar/open', "Copied to clipboard."))
    },
  },
});
</script>